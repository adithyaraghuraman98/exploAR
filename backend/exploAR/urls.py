from django.conf.urls import include, url
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    url(r'^get-places-json', views.get_places_json),
    url(r'^get-destination-json', views.get_destination_json),
    url(r'^get-place-details-json', views.get_place_details_json),
    url(r'^get-complete-place-info', views.get_complete_place_info),
    url(r'^register$',views.register,name='register'),
    url(r'^login$', auth_views.login, {'template_name':'exploAR/login.html'}, name='login'),
    url(r'^search$', views.search, name='search'),
    url(r'^place-info$', views.place_info, name="place-info"),
    url(r'^create-review$', views.createReview, name="createReview"),
    url(r'^logout$', auth_views.logout_then_login, name='logout'),
    url(r'^profilePage/(?P<username>\w+)$', views.profilePage, name='profilePage'),
    url(r'^addScout/(?P<id>\w+)$', views.addScout, name='addScout'),
    url(r'^removeScout/(?P<id>\w+)$', views.removeScout, name='removeScout'),
    url(r'^get-scouts-json', views.get_scouts_json),
    url(r'^searchScouts', views.search_users, name='searchScouts'),
    url(r'^scouts', views.home_friends, name='scouts'),
    url(r'^$', views.home, name='home')
]