from django.shortcuts import render
from rest_framework import generics,permissions,status
from rest_framework.response import Response
# from rest_framework import status
from .serializers import UserRegistrationSerializer,LoginSerializer,CustomUserSerializer, UserSearchSerializer,FriendRequestSerializer, FriendRequestCreateSerializer
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination 
from .models import CustomUser,FriendRequest
from rest_framework.exceptions import PermissionDenied
# from django.contrib.auth import get_user_model
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from django.core.cache import cache
from django.utils import timezone
from rest_framework.views import APIView


from rest_framework.permissions import IsAdminUser
from .models import CustomUser

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_friends(request):
    user = request.user
    friend_requests_sent = FriendRequest.objects.filter(from_user=user, status='accepted')
    friend_requests_received = FriendRequest.objects.filter(to_user=user, status='accepted')
    
    friends = [friend_request.to_user for friend_request in friend_requests_sent]
    friends.extend([friend_request.from_user for friend_request in friend_requests_received])
    
    serializer = CustomUserSerializer(friends, many=True)
    
    return Response(serializer.data)


class YourModelListView(generics.ListAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = LoginSerializer
    # permission_classes = [IsAdminUser]  # Only superusers can access this view
    permission_classes = [permissions.IsAuthenticated]


class UserRegistrationView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({'token': token.key}, status=status.HTTP_200_OK)
class UserSearchPagination(PageNumberPagination):
    page_size = 10

class UserSearchView(generics.ListAPIView):
    serializer_class = CustomUserSerializer
    pagination_class = UserSearchPagination

    def get_queryset(self):
        queryset = CustomUser.objects.all()
        serializer = UserSearchSerializer(data=self.request.query_params)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data.get('email')
        if email:
            queryset = queryset.filter(email__icontains=email)

        username = serializer.validated_data.get('username')
        if username:
            queryset = queryset.filter(name__icontains=username)

        return queryset

User = settings.AUTH_USER_MODEL
class SendFriendRequestView(generics.CreateAPIView,APIView):
    serializer_class = FriendRequestCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        from_user = request.user
        to_user_id = request.data.get('id')

        if not to_user_id:
            return Response({"detail": "to_user_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Rate limiting logic
        cache_key = f'friend_requests_{from_user.id}'
        request_times = cache.get(cache_key, [])

        # Filter out requests older than 1 minute
        one_minute_ago = timezone.now() - timezone.timedelta(minutes=1)
        request_times = [timestamp for timestamp in request_times if timestamp > one_minute_ago]

        if len(request_times) >= 3:
            return Response({"detail": "Rate limit exceeded. Try again later."}, status=status.HTTP_429_TOO_MANY_REQUESTS)

        # Add current timestamp and update cache
        request_times.append(timezone.now())
        cache.set(cache_key, request_times, timeout=60)  # Cache expires in 60 seconds

        # Create the friend request
        to_user = User.objects.get(id=to_user_id)
        friend_request, created = FriendRequest.objects.get_or_create(from_user=from_user, to_user=to_user, status='pending')
        if created:
            return Response({"detail": "Friend request sent"}, status=status.HTTP_201_CREATED)
        else:
            return Response({"detail": "Friend request already sent"}, status=status.HTTP_200_OK)
        

    def perform_create(self, serializer):
        serializer.save(from_user=self.request.user)  














class RespondToFriendRequestView(generics.UpdateAPIView):
    serializer_class = FriendRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = FriendRequest.objects.all()

    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        if instance.to_user != request.user:
            return Response({"detail": "You are not authorized to respond to this friend request."}, status=status.HTTP_403_FORBIDDEN)

        data = request.data
        if data.get('status') not in ['accepted', 'rejected']:
            return Response({"detail": "Invalid status."}, status=status.HTTP_400_BAD_REQUEST)

        instance.status = data['status']
        instance.save()
        return Response(FriendRequestSerializer(instance).data)

class ListFriendRequestsView(generics.ListAPIView):
    serializer_class = FriendRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return FriendRequest.objects.filter(to_user=self.request.user, status='pending')
    

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def respond_friend_request(request, pk):
    try:
        friend_request = FriendRequest.objects.get(pk=pk)
        if friend_request.to_user != request.user:
            return Response({'error': 'You do not have permission to respond to this friend request.'}, status=status.HTTP_403_FORBIDDEN)
        
        action = request.data.get('action')
        if action == 'accept':
            friend_request.status = 'accepted'
        elif action == 'reject':
            friend_request.status = 'rejected'
        else:
            return Response({'error': 'Invalid action.'}, status=status.HTTP_400_BAD_REQUEST)
        
        friend_request.save()
        return Response({'status': 'Friend request updated.'})
    except FriendRequest.DoesNotExist:
        return Response({'error': 'Friend request not found.'}, status=status.HTTP_404_NOT_FOUND)
    

class ListPendingFriendRequestsView(generics.ListAPIView):
    serializer_class = FriendRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return FriendRequest.objects.filter(to_user=self.request.user, status='pending')