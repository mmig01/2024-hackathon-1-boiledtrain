from django.http import HttpResponse, JsonResponse
import requests
from django.conf import settings
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import viewsets, mixins
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import api_view, permission_classes

from .models import Course, Diary
from .serializers import CourseSerializer, DiarySerializer

from django.shortcuts import get_object_or_404
# 거리 계산에 필요한 라이브러리
from math import radians, sin, cos, sqrt, atan2

class CourseViewSet(viewsets.ModelViewSet):
    # queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [AllowAny]
    lookup_field = 'id'

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Course.objects.filter(user=self.request.user)
        return Course.objects.all()
    #아직 로그인 기능이 구현되지 않아 모두가 접근할 수 있도록 설정해놓음

#다이어리 디테일, 여기서 수정,삭제
class DiaryViewSet(viewsets.GenericViewSet, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    # queryset = Diary.objects.all()
    serializer_class = DiarySerializer
    # permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    permission_classes = [AllowAny]

    def get_queryset(self):
        return Diary.objects.all()
    # def get_queryset(self):
        # return Diary.objects.filter(user=self.request.user) > 확인용으로 모두가 볼 수 있게 해놓음

#코스 별 다이어리 (댓글형식으로)
class CourseDiaryViewSet(viewsets.GenericViewSet, mixins.CreateModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    permission_classes = [AllowAny]
    serializer_class = DiarySerializer
# permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    def get_object(self):
        course_id = self.kwargs.get("course_id")
        return get_object_or_404(Diary, course_id=course_id)

    def create(self, request, *args, **kwargs):
        course = get_object_or_404(Course, id=self.kwargs.get("course_id"))
        if Diary.objects.filter(course=course).exists():
            return Response({"detail": "Diary already exists for this course."}, status=400)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(course=course)
        return Response(serializer.data, status=201)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response(status=204)


# M.K 파트

def haversine(lon1, lat1, lon2, lat2):
    # 지구 반지름 (킬로미터 단위)
    R = 6371.0

    # 위도와 경도를 라디안 단위로 변환
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    # 차이 계산
    dlon = lon2 - lon1
    dlat = lat2 - lat1

    # 하버사인 공식
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = R * c

    return distance

def is_good(lon1, lat1, lon2, lat2):

    # 두 지점 간 거리 계산
    distance = haversine(lon1, lat1, lon2, lat2)

    # 도보 시간 (시간 단위)
    walking_speed_kmh = 5  # 시속 5킬로미터
    walking_time_hours = 20 / 60  # 20분을 시간 단위로 변환

    # 20분 동안 도보 가능한 최대 거리
    max_walking_distance = walking_speed_kmh * walking_time_hours

    # 거리 비교
    if distance <= max_walking_distance:
        # 도보로 20분 이내면 True 반환
        return True
    else:
        return False

def search_station(subway_station):
    rest_api_key = getattr(settings, 'MAP_KEY')
    location_url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query={subway_station}&key={rest_api_key}&language=kr"
    location_response = requests.get(location_url).json()
    
    return location_response

def search_place(place):
    rest_api_key = getattr(settings, 'MAP_KEY')
    location_url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query={place}&key={rest_api_key}&language=ko"
    location_response = requests.get(location_url).json()

    return location_response

# 사진 출력 메소드, 미완성
def search_photo(request):
    rest_api_key = getattr(settings, 'MAP_KEY')
    # 최대 넓이
    max_width = 400
    photo_reference = "AelY_Cus4suL2Mw6X9RweWM05EaNMMsw3JpS4J9omAkMZw3_-7bVI4-4KS1-nt-x3tNgQE5Vo23wvFt1I5GAicwA3J-Hg3fc9qEYP1HI0Sah1YvoMKgxipTHshcSTiPJumxOKxnzsBfGfrBJhbdS9qrci62I8Ht3YlfANYQXpkFZ_M-abFQk"
    photo_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth={max_width}&photo_reference={photo_reference}&key={rest_api_key}&language=ko"
    photo_response = requests.get(photo_url)

    if photo_response.status_code == 200:
        # 이미지 데이터를 바로 반환
        return HttpResponse(photo_response.content, content_type='image/jpeg')
    else:
        return HttpResponse('Failed to retrieve the photo', status=photo_response.status_code)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def choose_and_add_place(request):
    # 사용자가 프론트 인터페이스에 입력한 장소 이름을 받아와서 구글 api를 통해 검색

    #프론트에서 받아올 부분
    #정확한 상호명을 받아와야 함
    subway_station = search_station("군자역") # Json 파일
    place = search_place("유가네닭갈비 군자") # Json 파일
    
    lng1 = subway_station['results'][0]['geometry']['location']['lng']
    lat1 = subway_station['results'][0]['geometry']['location']['lat']
    lng2 = place['results'][0]['geometry']['location']['lng']
    lat2 = place['results'][0]['geometry']['location']['lat']
    

    if is_good(lng1 , lat1 , lng2 , lat2): # 20분 이내 거리인지 확인
        result = {
            "subway_station" : {
                "name" : subway_station['results'][0]['name']
            },
            "place" : {
                "name" : place['results'][0]['name']
            }
        }
        if 'formatted_address' in place['results'][0]:
            result["place"]['address'] = place['results'][0]['formatted_address']
        if 'opening_hours' in place['results'][0]:
            result["place"]['opening_hours'] = place['results'][0]['opening_hours']
        if 'rating' in place['results'][0]:
            result["place"]['rating'] = place['results'][0]['rating']
        if 'user_ratings_total' in place['results'][0]:
            result["place"]['user_ratings_total'] = place['results'][0]['user_ratings_total']
        if 'types' in place['results'][0]:
            result["place"]['types'] = place['results'][0]['types']
        if 'photo_reference' in place['results'][0]['photos'][0]:
            result['place']['photo_reference'] = place['results'][0]['photos'][0]['photo_reference']
        # db 에 추가하는 동작이 필요함

        course = get_object_or_404(Course, user=request.user)
        

        return JsonResponse(result)

    else:
        return JsonResponse({"error" : "두 지점은 도보로 20분 이상의 거리입니다."})

