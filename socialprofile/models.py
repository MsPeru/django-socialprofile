"""Django Models for SocialProfile App"""

# pylint: disable=W0613

from django.db.models.signals import post_save
from social_auth.backends.facebook import FacebookBackend
from social_auth.backends.google import GoogleOAuth2Backend
from social_auth.backends.twitter import TwitterBackend
from django.db import models
from django.contrib.auth.models import User
from social_auth.signals import socialauth_registered
from urllib import urlencode
from urllib2 import Request, urlopen
from django.utils import simplejson
import logging

log = logging.getLogger(name='socialprofile')

class UserProfile(models.Model):
    """Main UserProfile Object - Holds extra profile data retrived from auth providers"""
    GENDER_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
        ('', '')
        )
    user = models.OneToOneField(User)
    gender = models.CharField(max_length=10, blank=True, choices=GENDER_CHOICES)
    url = models.URLField(blank=True)
    image_url = models.URLField(blank=True)
    description = models.TextField(blank=True)


def create_user_profile(sender, instance, created, **kwargs):
    """Creates a UserProfile Object Whenever a User Object is Created"""
    if created:
        UserProfile.objects.create(user=instance)

post_save.connect(create_user_profile, sender=User)

def facebook_extra_values(sender, user, response, details, **kwargs):
    """Populates a UserProfile Object when a new User is created via Facebook Auth"""
    user.last_name = response.get('last_name', '')
    user.first_name = response.get('first_name', '')
    profile = user.get_profile()
    profile.gender = response.get('gender', '')
    if response.get('username') is not None:
        profile.image_url = 'https://graph.facebook.com/' + response.get('username') + '/picture'
    profile.url = response.get('link', '')
    if response.get('hometown') is not None:
        profile.description = response.get('hometown').get('name')

    profile.save()

    return True

socialauth_registered.connect(facebook_extra_values, sender=FacebookBackend)

def google_extra_values(sender, user, response, details, **kwargs):
    """Populates a UserProfile Object when a new User is created via Google Auth"""
#    log.debug('Inside Google Extra Values Handler')
    user_info_url = "https://www.googleapis.com/oauth2/v1/userinfo"

    data = {'access_token': response.get('access_token', ''), 'alt': 'json'}
    params = urlencode(data)
    try:
        request = Request(user_info_url + '?' + params, headers={'Authorization': params})
        result = simplejson.loads(urlopen(request).read())

        user.last_name = result.get('family_name', '')
        user.first_name = result.get('given_name', '')
        profile = user.get_profile()
        profile.gender = result.get('gender', '')
        profile.image_url = result.get('picture', '')
        profile.url = result.get('link', '')

        profile.save()
    except:
        pass

    return True

socialauth_registered.connect(google_extra_values, sender=GoogleOAuth2Backend)

def twitter_extra_values(sender, user, response, details, **kwargs):
    """Populates a UserProfile Object when a new User is created via Twitter Auth"""
    try:
        first_name, last_name = response.get('name', '').split(' ', 1)
    except:
        first_name = response.get('name', '')
        last_name = ''
    user.last_name = last_name
    user.first_name = first_name
    profile = user.get_profile()
    if response.get('screen_name') is not None:
        profile.url = 'http://twitter.com/' + response.get('screen_name', '')
    profile.image_url = response.get('profile_image_url_https', '')
    profile.description = response.get('description', '')

    profile.save()

    return True

socialauth_registered.connect(twitter_extra_values, sender=TwitterBackend)