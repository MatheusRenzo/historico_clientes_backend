from rest_framework.routers import DefaultRouter
from .views import JiraConnectionViewSet, JiraIssueViewSet

router = DefaultRouter()
router.register(r"jira/connections", JiraConnectionViewSet, basename="jira-connections")
router.register(r"jira/issues", JiraIssueViewSet, basename="jira-issues")

urlpatterns = router.urls
