from django.urls import path, include
from rest_framework import routers
from .views import CourseViewSet, DiaryViewSet, CourseDiaryViewSet, choose_and_add_place, search_photo

from django.conf.urls.static import static
from django.conf import settings

app_name="user"

course_router = routers.SimpleRouter(trailing_slash=False)
course_router.register("course", CourseViewSet, basename="course")

diary_router = routers.SimpleRouter(trailing_slash=False)
diary_router.register("diary", DiaryViewSet, basename="diary")

urlpatterns = [
    # M.K 파트
    # 코스 관련 url
    path('', include(course_router.urls)),
    # 사진 출력
    path("search_photo" ,search_photo, name="search_photo"),

    # 아래 수정해야함
    path('course/<int:id>/', CourseViewSet.as_view({'get': 'retrieve'}), name='course-detail'),
    path('course/<int:course_id>/diary/', CourseDiaryViewSet.as_view({'get': 'retrieve', 'post': 'create', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='course-diary'),
    path('choose_and_add_place/', choose_and_add_place, name="choose_and_add_place"),
    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


