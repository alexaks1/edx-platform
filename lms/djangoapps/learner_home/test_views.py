"""Test for learner views and related functions"""

from contextlib import contextmanager
import json
from unittest import TestCase
from unittest.mock import patch
from uuid import uuid4

import ddt
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from opaque_keys.edx.keys import CourseKey
from rest_framework.test import APITestCase

from common.djangoapps.course_modes.models import CourseMode
from common.djangoapps.entitlements.tests.factories import CourseEntitlementFactory
from common.djangoapps.student.tests.factories import (
    CourseEnrollmentFactory,
    UserFactory,
)
from lms.djangoapps.bulk_email.models import Optout
from lms.djangoapps.learner_home.test_utils import create_test_enrollment
from lms.djangoapps.learner_home.views import (
    get_course_overviews_for_pseudo_sessions,
    get_course_programs,
    get_email_settings_info,
    get_enrollments,
    get_platform_settings,
    get_suggested_courses,
    get_user_account_confirmation_info,
    get_entitlements,
)
from lms.djangoapps.learner_home.test_serializers import random_url
from openedx.core.djangoapps.catalog.tests.factories import (
    CourseRunFactory as CatalogCourseRunFactory,
    ProgramFactory,
)
from openedx.core.djangoapps.content.course_overviews.tests.factories import (
    CourseOverviewFactory,
)
from openedx.core.djangoapps.site_configuration.tests.factories import SiteFactory
from xmodule.modulestore.tests.django_utils import (
    TEST_DATA_SPLIT_MODULESTORE,
    SharedModuleStoreTestCase,
)
from xmodule.modulestore.tests.factories import CourseFactory
from openedx.core.djangoapps.catalog.tests.factories import (
    CourseFactory as CatalogCourseFactory,
)


ENTERPRISE_ENABLED = "ENABLE_ENTERPRISE_INTEGRATION"


class TestGetPlatformSettings(TestCase):
    """Tests for get_platform_settings"""

    MOCK_SETTINGS = {
        "DEFAULT_FEEDBACK_EMAIL": f"{uuid4()}@example.com",
        "PAYMENT_SUPPORT_EMAIL": f"{uuid4()}@example.com",
    }

    @patch.multiple("django.conf.settings", **MOCK_SETTINGS)
    @patch("lms.djangoapps.learner_home.views.marketing_link")
    def test_happy_path(self, mock_marketing_link):
        # Given email/search info exists
        mock_marketing_link.return_value = mock_search_url = f"/{uuid4()}"

        # When I request those settings
        return_data = get_platform_settings()

        # Then I return them in the appropriate format
        self.assertDictEqual(
            return_data,
            {
                "supportEmail": self.MOCK_SETTINGS["DEFAULT_FEEDBACK_EMAIL"],
                "billingEmail": self.MOCK_SETTINGS["PAYMENT_SUPPORT_EMAIL"],
                "courseSearchUrl": mock_search_url,
            },
        )


@ddt.ddt
class TestGetUserAccountConfirmationInfo(SharedModuleStoreTestCase):
    """Tests for get_user_account_confirmation_info"""

    MOCK_SETTINGS = {
        "ACTIVATION_EMAIL_SUPPORT_LINK": "activation.example.com",
        "SUPPORT_SITE_LINK": "support.example.com",
    }

    @classmethod
    def mock_response(cls):
        return {
            "isNeeded": False,
            "sendEmailUrl": random_url(),
        }

    def setUp(self):
        super().setUp()
        self.user = UserFactory()

    @patch.multiple("django.conf.settings", **MOCK_SETTINGS)
    @ddt.data(True, False)
    def test_is_needed(self, user_is_active):
        """Email confirmation is needed when the user is not active"""
        self.user.is_active = user_is_active

        user_account_confirmation_info = get_user_account_confirmation_info(self.user)

        assert user_account_confirmation_info["isNeeded"] == (not user_is_active)

    @patch(
        "django.conf.settings.ACTIVATION_EMAIL_SUPPORT_LINK",
        MOCK_SETTINGS["ACTIVATION_EMAIL_SUPPORT_LINK"],
    )
    def test_email_url_support_link(self):
        # Given an ACTIVATION_EMAIL_SUPPORT_LINK is supplied
        # When I get user account confirmation info
        user_account_confirmation_info = get_user_account_confirmation_info(self.user)

        # Then that link should be returned as the sendEmailUrl
        self.assertEqual(
            user_account_confirmation_info["sendEmailUrl"],
            self.MOCK_SETTINGS["ACTIVATION_EMAIL_SUPPORT_LINK"],
        )

    @patch("lms.djangoapps.learner_home.views.configuration_helpers")
    @patch("django.conf.settings.SUPPORT_SITE_LINK", MOCK_SETTINGS["SUPPORT_SITE_LINK"])
    def test_email_url_support_fallback_link(self, mock_config_helpers):
        # Given an ACTIVATION_EMAIL_SUPPORT_LINK is NOT supplied
        mock_config_helpers.get_value.return_value = None

        # When I get user account confirmation info
        user_account_confirmation_info = get_user_account_confirmation_info(self.user)

        # Then sendEmailUrl falls back to SUPPORT_SITE_LINK
        self.assertEqual(
            user_account_confirmation_info["sendEmailUrl"],
            self.MOCK_SETTINGS["SUPPORT_SITE_LINK"],
        )


class TestGetEnrollments(SharedModuleStoreTestCase):
    """Tests for get_enrollments"""

    def setUp(self):
        super().setUp()
        self.user = UserFactory()

    def test_basic(self):
        # Given a set of enrollments
        test_enrollments = [create_test_enrollment(self.user) for i in range(3)]

        # When I request my enrollments
        returned_enrollments, course_mode_info = get_enrollments(self.user, None, None)

        # Then I return those enrollments and course mode info
        assert len(returned_enrollments) == len(test_enrollments)
        assert len(course_mode_info.keys()) == len(test_enrollments)

        # ... with enrollments and course info
        for enrollment in test_enrollments:
            assert enrollment.course_id in course_mode_info
            assert enrollment in returned_enrollments

    def test_empty(self):
        # Given a user has no enrollments
        # When they request enrollments
        returned_enrollments, course_mode_info = get_enrollments(self.user, None, None)

        # Then I return an empty list and dict
        self.assertEqual(returned_enrollments, [])
        self.assertEqual(course_mode_info, {})


class TestGetEntitlements(SharedModuleStoreTestCase):
    """Tests for get_entitlements"""

    def setUp(self):
        super().setUp()
        self.user = UserFactory()

    @contextmanager
    def mock_get_filtered_course_entitlements(
        self,
        filtered_entitlements,
        course_entitlement_available_sessions,
        unfulfilled_entitlement_pseudo_sessions,
    ):
        """
        Context manager utility for mocking get_filtered_course_entitlements.
        This function calls out to multiple external services and is tested elsewhere.
        """
        return_value = (
            filtered_entitlements,
            course_entitlement_available_sessions,
            unfulfilled_entitlement_pseudo_sessions,
        )
        with patch(
            "lms.djangoapps.learner_home.views.get_filtered_course_entitlements",
            return_value=return_value,
        ):
            yield

    def create_test_fulfilled_entitlement(self):
        enrollment = CourseEnrollmentFactory(user=self.user, is_active=True)
        return CourseEntitlementFactory.create(
            user=self.user, enrollment_course_run=enrollment
        )

    def create_test_unfulfilled_entitlement(self):
        return CourseEntitlementFactory.create(user=self.user)

    def create_test_entitlement(self):
        """create an entitlement course for the user"""
        enrollment = CourseEnrollmentFactory(user=self.user, is_active=True)
        return CourseEntitlementFactory.create(
            user=self.user, enrollment_course_run=enrollment, expired_at=timezone.now()
        )

    def test_basic(self):
        fulfilled_test_entitlements = [
            self.create_test_fulfilled_entitlement() for _ in range(2)
        ]
        unfulfilled_test_entitlements = [
            self.create_test_unfulfilled_entitlement() for _ in range(3)
        ]

        available_sessions = {}
        for entitlement in fulfilled_test_entitlements + unfulfilled_test_entitlements:
            available_sessions[
                str(entitlement.uuid)
            ] = CatalogCourseRunFactory.create_batch(3)

        pseudo_sessions = {}
        for entitlement in unfulfilled_test_entitlements:
            pseudo_sessions[str(entitlement.uuid)] = CatalogCourseRunFactory.create()

        with self.mock_get_filtered_course_entitlements(
            fulfilled_test_entitlements + unfulfilled_test_entitlements,
            available_sessions,
            pseudo_sessions,
        ):
            (
                fulfilled_entitlements_by_course_key,
                unfulfilled_entitlements,
                course_entitlement_available_sessions,
                unfulfilled_entitlement_pseudo_sessions,
            ) = get_entitlements(self.user, None, None)

        assert len(fulfilled_entitlements_by_course_key) == len(
            fulfilled_test_entitlements
        )
        assert len(unfulfilled_entitlements) == len(unfulfilled_test_entitlements)
        assert set(unfulfilled_entitlements) == set(unfulfilled_test_entitlements)
        assert course_entitlement_available_sessions is available_sessions
        assert unfulfilled_entitlement_pseudo_sessions is pseudo_sessions

        for fulfilled_entitlement in fulfilled_test_entitlements:
            course_id = str(fulfilled_entitlement.enrollment_course_run.course.id)
            entitlement = fulfilled_entitlements_by_course_key[course_id]
            assert entitlement is fulfilled_entitlement

    def test_empty(self):
        with self.mock_get_filtered_course_entitlements([], {}, {}):
            (
                fulfilled_entitlements_by_course_key,
                unfulfulled_entitlements,
                course_entitlement_available_sessions,
                unfulfilled_entitlement_pseudo_sessions,
            ) = get_entitlements(self.user, None, None)

        assert not fulfilled_entitlements_by_course_key
        assert not unfulfulled_entitlements
        assert not course_entitlement_available_sessions
        assert not unfulfilled_entitlement_pseudo_sessions


class TestGetCourseOverviewsForPseudoSessions(SharedModuleStoreTestCase):
    """Tests for get_course_overviews_for_pseudo_sessions"""

    def test_basic(self):
        # Given several unfulfilled entitlements
        unfulfilled_entitlement_uuids = [uuid4() for _ in range(3)]
        pseudo_sessions = {}
        for uuid in unfulfilled_entitlement_uuids:
            pseudo_sessions[str(uuid)] = CatalogCourseRunFactory.create()

        # ... that have matching CourseOverviews
        expected_course_overviews = {}
        for pseudo_session in pseudo_sessions.values():
            course_key = CourseKey.from_string(pseudo_session["key"])
            mock_course = CourseFactory.create(
                org=course_key.org, run=course_key.run, number=course_key.course
            )
            mock_course_overview = CourseOverviewFactory.create(id=mock_course.id)
            expected_course_overviews[course_key] = mock_course_overview

        # When I try to get course overviews, keyed by course key
        course_overviews = get_course_overviews_for_pseudo_sessions(pseudo_sessions)

        # Then they map to the correct courses
        self.assertDictEqual(course_overviews, expected_course_overviews)

    def test_no_pseudo_sessions(self):
        # Given no pseudo sessions
        pseudo_sessions = {}

        # When I query course overviews
        course_overviews = get_course_overviews_for_pseudo_sessions(pseudo_sessions)

        # Then I should get an empty dict
        self.assertDictEqual(course_overviews, {})


class TestGetEmailSettingsInfo(SharedModuleStoreTestCase):
    """Tests for get_email_settings_info"""

    def setUp(self):
        super().setUp()
        self.user = UserFactory()

    @patch("lms.djangoapps.learner_home.views.is_bulk_email_feature_enabled")
    def test_get_email_settings(self, mock_is_bulk_email_enabled):
        # Given 3 courses where bulk email is enabled for 2 and user has opted out of one
        courses = [CourseFactory.create() for _ in range(3)]
        enrollments = [
            CourseEnrollmentFactory.create(user=self.user, course_id=course.id)
            for course in courses
        ]
        optouts = {Optout.objects.create(user=self.user, course_id=courses[1].id)}
        mock_is_bulk_email_enabled.side_effect = (True, True, False)

        # When I get email settings
        show_email_settings_for, course_optouts = get_email_settings_info(
            self.user, enrollments
        )

        # Then the email settings show for courses where bulk email is enabled
        self.assertSetEqual(
            {course.id for course in courses[0:2]}, show_email_settings_for
        )

        # ... and course optouts are returned
        self.assertSetEqual(
            {optout.course_id for optout in optouts},
            set(course_optouts),
        )


class TestGetSuggestedCourses(SharedModuleStoreTestCase):
    """Tests for get_suggested_courses"""

    MOCK_SUGGESTED_COURSES = {
        "courses": [
            {
                "course_key": "HogwartsX+6.00.1x",
                "logo_image_url": random_url(),
                "marketing_url": random_url(),
                "title": "Defense Against the Dark Arts",
            },
            {
                "course_key": "MonstersX+SC101EN",
                "logo_image_url": random_url(),
                "marketing_url": random_url(),
                "title": "Scaring 101",
            },
        ],
        "is_personalized_recommendation": False,
    }

    EMPTY_SUGGESTED_COURSES = {
        "courses": [],
        "is_personalized_recommendation": False,
    }

    @patch("django.conf.settings.GENERAL_RECOMMENDATION", MOCK_SUGGESTED_COURSES)
    def test_suggested_courses(self):
        # Given suggested courses are configured
        # When I request suggested courses
        return_data = get_suggested_courses()

        # Then I return them in the appropriate response
        self.assertDictEqual(return_data, self.MOCK_SUGGESTED_COURSES)

    def test_no_suggested_courses(self):
        # Given suggested courses are not found/configured
        # When I request suggested courses
        return_data = get_suggested_courses()

        # Then I return them in the appropriate response
        self.assertDictEqual(return_data, self.EMPTY_SUGGESTED_COURSES)


class TestDashboardView(SharedModuleStoreTestCase, APITestCase):
    """Tests for the dashboard view"""

    MODULESTORE = TEST_DATA_SPLIT_MODULESTORE

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Get view URL
        cls.view_url = reverse("learner_home:initialize")

        # Set up a course
        cls.course = CourseFactory.create()
        cls.course_key = cls.course.location.course_key

        # Set up a user
        cls.username = "alan"
        cls.password = "enigma"
        cls.user = UserFactory(username=cls.username, password=cls.password)
        cls.site = SiteFactory()

    def log_in(self):
        """Log in as a test user"""
        self.client.login(username=self.username, password=self.password)

    def setUp(self):
        super().setUp()
        self.log_in()

    def _create_course_programs(self, course_uuid=None):
        """
        Create a program with entitlements
        """
        course_uuid = course_uuid or str(uuid4())

        program = ProgramFactory(courses=[CatalogCourseFactory(uuid=str(course_uuid))])

        enrollment = CourseEnrollmentFactory(
            user=self.user, mode=CourseMode.VERIFIED, is_active=False
        )

        entitlement = CourseEntitlementFactory.create(
            user=self.user,
            course_uuid=course_uuid,
            mode=CourseMode.VERIFIED,
            enrollment_course_run=enrollment,
        )

        return (program, enrollment, entitlement)

    @patch.dict(settings.FEATURES, ENTERPRISE_ENABLED=False)
    def test_response_structure(self):
        """Basic test for correct response structure"""

        # Given I am logged in
        self.log_in()

        # When I request the dashboard
        response = self.client.get(self.view_url)

        # Then I get the expected success response
        assert response.status_code == 200

        response_data = json.loads(response.content)
        expected_keys = set(
            [
                "emailConfirmation",
                "enterpriseDashboard",
                "platformSettings",
                "courses",
                "suggestedCourses",
            ]
        )

        assert expected_keys == response_data.keys()

    @patch.dict(settings.FEATURES, ENTERPRISE_ENABLED=False)
    @patch("lms.djangoapps.learner_home.views.get_user_account_confirmation_info")
    def test_email_confirmation(self, mock_user_conf_info):
        """Test that email confirmation info passes through correctly"""

        # Given I am logged in
        self.log_in()

        # (and we have tons of mocks to avoid integration tests)
        mock_user_conf_info_response = (
            TestGetUserAccountConfirmationInfo.mock_response()
        )
        mock_user_conf_info.return_value = mock_user_conf_info_response

        # When I request the dashboard
        response = self.client.get(self.view_url)

        # Then I get the expected success response
        assert response.status_code == 200
        response_data = json.loads(response.content)

        self.assertDictEqual(
            response_data["emailConfirmation"],
            {
                "isNeeded": mock_user_conf_info_response["isNeeded"],
                "sendEmailUrl": mock_user_conf_info_response["sendEmailUrl"],
            },
        )

    @patch.dict(settings.FEATURES, ENTERPRISE_ENABLED=False)
    @patch("lms.djangoapps.learner_home.views.cert_info")
    def test_get_cert_statuses(self, mock_get_cert_info):
        """Test that cert information gets loaded correctly"""

        # Given I am logged in
        self.log_in()

        # (and we have tons of mocks to avoid integration tests)
        mock_enrollment = create_test_enrollment(
            self.user, course_mode=CourseMode.VERIFIED
        )
        mock_cert_info = {
            "status": "downloadable",
            "mode": "verified",
            "linked_in_url": None,
            "show_survey_button": False,
            "can_unenroll": True,
            "show_cert_web_view": True,
            "cert_web_view_url": random_url(),
        }
        mock_get_cert_info.return_value = mock_cert_info

        # When I request the dashboard
        response = self.client.get(self.view_url)

        # Then I get the expected success response
        assert response.status_code == 200
        response_data = json.loads(response.content)

        self.assertDictEqual(
            response_data["courses"][0]["certificate"],
            {
                "availableDate": mock_enrollment.course.certificate_available_date,
                "isRestricted": False,
                "isEarned": True,
                "isDownloadable": True,
                "certPreviewUrl": mock_cert_info["cert_web_view_url"],
            },
        )

    @patch.dict(settings.FEATURES, ENTERPRISE_ENABLED=False)
    @patch("openedx.core.djangoapps.programs.utils.get_programs")
    def test_get_for_one_of_course_programs(self, mock_get_programs):
        """Test that course programs get loaded correctly"""

        # Given I am logged in
        self.log_in()

        course_uuid = str(uuid4())
        program, enrollment, _ = self._create_course_programs(course_uuid=course_uuid)

        data = [
            program,
            ProgramFactory(),
        ]
        mock_get_programs.return_value = data

        programs = get_course_programs(self.user, [enrollment], self.site)

        assert len(programs) == 1
        assert programs[course_uuid][0] == program
        assert len(data) > len(programs)

    @patch.dict(settings.FEATURES, ENTERPRISE_ENABLED=False)
    @patch("openedx.core.djangoapps.programs.utils.get_programs")
    def test_get_multiple_course_programs(self, mock_get_programs):
        """Test that course programs get loaded correctly"""

        # Given I am logged in
        self.log_in()

        course_uuid = str(uuid4())
        course_uuid2 = str(uuid4())
        program, enrollment, _ = self._create_course_programs(course_uuid=course_uuid)
        program2, enrollment2, _ = self._create_course_programs(
            course_uuid=course_uuid2
        )

        data = [
            program,
            program2,
        ]
        mock_get_programs.return_value = data

        programs = get_course_programs(self.user, [enrollment, enrollment2], self.site)

        assert len(data) == len(programs)
        assert programs[course_uuid][0] == program
        assert programs[course_uuid2][0] == program2
