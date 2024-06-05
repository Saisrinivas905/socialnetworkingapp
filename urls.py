# urls.py
from django.urls import path
from .views import UserRegistrationView,LoginView,UserSearchView,SendFriendRequestView, RespondToFriendRequestView, ListFriendRequestsView
from .views import list_friends,respond_friend_request,ListPendingFriendRequestsView
urlpatterns = [
    path('signup/', UserRegistrationView.as_view(), name='user-signup'),
    path('login/', LoginView.as_view(), name='user-login'),
    path('users/search/', UserSearchView.as_view(), name='user-search'),
    path('friend-request/send/', SendFriendRequestView.as_view(), name='send-friend-request'),
    path('friend-request/respond/<int:pk>/', RespondToFriendRequestView.as_view(), name='respond-friend-request'),
    path('friend-request/list/', ListFriendRequestsView.as_view(), name='list-friend-requests'),
     path('friends/', list_friends, name='list-friends'),
     path('friend-request/respond/<int:pk>/', respond_friend_request, name='respond-friend-request'),
    path('friend-requests/pending/', ListPendingFriendRequestsView.as_view(), name='list-pending-friend-requests'),
    
]
