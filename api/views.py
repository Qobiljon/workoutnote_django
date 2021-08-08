from django.views.decorators.http import require_http_methods
from django.contrib.auth import login, logout, authenticate
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User as django_User
from workoutnote_django import models as wn_models, settings
from django.core.mail import EmailMessage
from datetime import datetime, timedelta
from django.http import JsonResponse
from utils.tools import Tools
from api import models
import random
import time
import json


# region auth
@csrf_exempt
@require_http_methods(['POST'])
def handle_login_api(request):
    required_params = ['email', 'password']
    received_params = json.loads(request.body.decode('utf8'))
    if False not in [x in received_params for x in required_params]:
        email = received_params['email']
        password = received_params['password']
        user = authenticate(username=email, password=password)
        if user and user.is_authenticated:
            login(request=request, user=user)
            if not models.SessionKey.objects.filter(user=user).exists():
                session_key = models.SessionKey.generate_key(email=email)
                while models.SessionKey.objects.filter(key=session_key).exists():
                    time.sleep(0.001)
                    session_key = models.SessionKey.generate_key(email=email)
                models.SessionKey.objects.create(user=user, key=session_key)
            else:
                session_key = models.SessionKey.objects.get(user=user).key
            return JsonResponse(data={'success': True, 'sessionKey': session_key})
        else:
            return JsonResponse(data={'success': False})
    else:
        return JsonResponse(data={'success': False, 'reason': 'bad params, must provide email and password'})


@csrf_exempt
@require_http_methods(['POST'])
def handle_send_verification_code_api(request):
    required_params = ['email']
    received_params = json.loads(request.body.decode('utf8'))
    if False not in [x in received_params for x in required_params]:
        email = received_params['email']
        if not wn_models.EmailConfirmationCodes.objects.filter(email=email).exists():
            verification_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
            email_message = EmailMessage(
                'Workoutnote.com email verification',
                f'Email verification code is : {verification_code}',
                settings.EMAIL_HOST_USER,
                [email],
            )
            email_message.fail_silently = False
            email_message.send()
            wn_models.EmailConfirmationCodes.objects.create(email=email, verification_code=verification_code)
            return JsonResponse(data={'success': True})
        else:
            return JsonResponse(data={'success': False, 'reason': 'already sent'})
    else:
        return JsonResponse(data={'success': False, 'reason': 'bad params, must provide email and password'})


@csrf_exempt
@require_http_methods(['POST'])
def handle_verify_register_api(request):
    required_params = ['name', 'email', 'password', 'verification_code']
    received_params = json.loads(request.body.decode('utf8'))
    if False not in [x in received_params for x in required_params]:
        name = received_params['name']
        email = received_params['email']
        password = received_params['password']
        if django_User.objects.filter(username=email).exists() or len(password) < 4:
            return JsonResponse(data={'success': False, 'reason': 'user already exists or password is too short'})
        else:
            expected_code = wn_models.EmailConfirmationCodes.objects.get(email=email).verification_code
            provided_code = received_params['verification_code']
            if provided_code == expected_code:
                wn_models.EmailConfirmationCodes.objects.filter(email=email).delete()
                django_User.objects.create_user(username=email, password=password)
                user = authenticate(request, username=email, password=password)
                if user:
                    wn_models.Preferences.objects.create(user=user, name=name)
                    return JsonResponse(data={'success': True})
                else:
                    return JsonResponse(data={'success': False, 'reason': 'Unknown, please contact backend developer!'})  # whatever the reason could be
            else:
                return JsonResponse(data={'success': False, 'reason': 'incorrect verification code'})
    else:
        return JsonResponse(data={'success': False, 'reason': 'bad params, must provide email and password'})


# endregion


# region settings
@csrf_exempt
@require_http_methods(['POST'])
def handle_fetch_settings_api(request):
    received_params = json.loads(request.body.decode('utf8'))
    if 'sessionKey' in received_params:
        session_key = received_params['sessionKey']
        if models.SessionKey.objects.filter(key=session_key).exists():
            user = models.SessionKey.objects.get(key=session_key).user
            if wn_models.Preferences.objects.filter(user=user).exists():
                preferences = wn_models.Preferences.objects.get(user=user)
                return JsonResponse(data={
                    'success': True,
                    'name': preferences.name,
                    'date_of_birth': preferences.date_of_birth,
                    'gender': preferences.gender,
                    'is_profile_shared': preferences.shared_profile,
                })
            else:
                return JsonResponse(data={'success': False, 'reason': 'no settings associated with user, please contact the developer'})
        else:
            return JsonResponse(data={'success': False, 'reason': 'double check sessionKey value'})
    else:
        return JsonResponse(data={'success': False, 'reason': 'bad params, must provide sessionKey'})


@csrf_exempt
@require_http_methods(['POST'])
def handle_update_settings_api(request):
    received_params = json.loads(request.body.decode('utf8'))
    if 'sessionKey' in received_params:
        session_key = received_params['sessionKey']
        if models.SessionKey.objects.filter(key=session_key).exists():
            user = models.SessionKey.objects.get(key=session_key).user
            if wn_models.Preferences.objects.filter(user=user).exists():
                preferences = wn_models.Preferences.objects.get(user=user)
                if 'name' in received_params:
                    preferences.name = received_params['name']
                if 'date_of_birth' in received_params:
                    preferences.date_of_birth = received_params['date_of_birth']
                if 'gender' in received_params:
                    preferences.gender = received_params['gender']
                if 'is_profile_shared' in received_params:
                    preferences.shared_profile = received_params['is_profile_shared']
                preferences.save()
                return JsonResponse(data={'success': True})
            else:
                return JsonResponse(data={'success': False, 'reason': 'no settings associated with user, please contact the developer'})
        else:
            return JsonResponse(data={'success': False, 'reason': 'double check sessionKey value'})
    else:
        return JsonResponse(data={'success': False, 'reason': 'bad params, must provide sessionKey'})


# endregion


# region exercises & body parts
@csrf_exempt
@require_http_methods(['POST'])
def handle_fetch_exercises_api(request):
    exercises = wn_models.Exercise.objects.all()
    exercises_arr = []
    for exercise in exercises:
        exercises_arr += [{
            'id': exercise.id,
            'name': exercise.name,
            'name_translations': exercise.name_translations,
            'body_part_str': exercise.body_part.name,
            'category_str': exercise.category.name,
            'icon_str': exercise.icon.name,
        }]
    return JsonResponse(data={
        'success': True,
        'exercises': exercises_arr
    })


@csrf_exempt
@require_http_methods(['POST'])
def handle_fetch_body_parts_api(request):
    body_parts = wn_models.BodyPart.objects.all()
    body_parts_arr = []
    for body_part in body_parts:
        body_parts_arr += [{
            'id': body_part.id,
            'name': body_part.name,
        }]
    return JsonResponse(data={
        'success': True,
        'body_parts': body_parts_arr
    })


# endregion


# region workout
@csrf_exempt
@require_http_methods(['POST'])
def handle_insert_workout_api(request):
    required_params = ['title', 'duration']
    received_params = json.loads(request.body.decode('utf8'))
    if False not in [x in received_params for x in required_params]:
        session_key = received_params['sessionKey']
        if models.SessionKey.objects.filter(key=session_key).exists():
            user = models.SessionKey.objects.get(key=session_key).user
            workout_session = wn_models.WorkoutSession.objects.create(
                user=user,
                timestamp=int(datetime.now().timestamp() * 1000),
                title=received_params['title'],
                duration=int(received_params['duration']),
            )
            return JsonResponse(data={
                'success': True,
                'workout_session': {
                    'id': workout_session.id,
                    'title': workout_session.title,
                    'timestamp': int(workout_session.timestamp.timestamp() * 1000),
                    'duration': workout_session.duration,
                }
            })
        else:
            return JsonResponse(data={'success': False, 'reason': 'double check sessionKey value'})
    else:
        return JsonResponse(data={'success': False, 'reason': f'bad params, must provide {",".join(required_params)}'})


@csrf_exempt
def handle_fetch_workouts_api(request):
    required_params = ['sessionKey', 'dateTimestampMs']
    received_params = json.loads(request.body.decode('utf8'))
    if False not in [x in received_params for x in required_params]:
        session_key = received_params['sessionKey']
        date = datetime.utcfromtimestamp(int(received_params['dateTimestampMs']) / 1000)
        date_from_ts = date.replace(hour=0, minute=0, second=0, microsecond=0)
        date_till_ts = date.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        if models.SessionKey.objects.filter(key=session_key).exists():
            user = models.SessionKey.objects.get(key=session_key).user
            workout_sessions = []
            for workout_session in wn_models.WorkoutSession.objects.filter(user=user, timestamp__gte=date_from_ts, timestamp__lt=date_till_ts):
                lifts = []
                for lift in wn_models.Lift.objects.filter(workout_session=workout_session):
                    lifts += [{
                        'id': lift.id,
                        'timestamp': int(lift.timestamp.timestamp() * 1000),
                        'one_rep_max': lift.one_rep_max,
                        'exercise_id': lift.exercise.id,
                        'exercise_name': lift.exercise.name,
                        'exercise_name_translations': lift.exercise.name_translations,
                        'lift_mass': lift.lift_mass,
                        'repetitions': lift.repetitions,
                    }]
                workout_sessions += [
                    {
                        'id': workout_session.id,
                        'title': workout_session.title,
                        'timestamp': int(workout_session.timestamp.timestamp() * 1000),
                        'duration': workout_session.duration,
                        'lifts': lifts
                    }
                ]
            return JsonResponse(data={
                'success': True,
                'workouts': workout_sessions
            })
        else:
            return JsonResponse(data={'success': False, 'reason': 'double check sessionKey value'})
    else:
        return JsonResponse(data={'success': False, 'reason': f'bad params, must provide {",".join(required_params)}'})


# endregion


# region lifts
@csrf_exempt
@require_http_methods(['POST'])
def handle_insert_lift_api(request):
    required_params = ['sessionKey', 'exercise_id', 'workout_session_id', 'lift_mass', 'repetitions']
    received_params = json.loads(request.body.decode('utf8'))
    if False not in [x in received_params for x in required_params]:
        session_key = received_params['sessionKey']
        if models.SessionKey.objects.filter(key=session_key).exists():
            user = models.SessionKey.objects.get(key=session_key).user
            if wn_models.Exercise.objects.filter(id=received_params['exercise_id']).exists() and wn_models.WorkoutSession.objects.filter(id=int(received_params['workout_session_id']), user=user).exists():
                exercise = wn_models.Exercise.objects.get(id=received_params['exercise_id'])
                workout_session = wn_models.WorkoutSession.objects.get(id=int(received_params['workout_session_id']))
                lift_mass = float(received_params['lift_mass'])
                repetitions = int(received_params['repetitions'])
                lift = wn_models.Lift.objects.create(
                    timestamp=int(datetime.now().timestamp() * 1000),
                    workout_session=workout_session,
                    exercise=exercise,
                    lift_mass=lift_mass,
                    repetitions=repetitions,
                    one_rep_max=Tools.calculate_one_rep_max(lift_mass=lift_mass, repetitions=repetitions),
                )
                return JsonResponse(data={
                    'success': True,
                    'lift': {
                        'id': lift.id,
                        'timestamp': int(lift.timestamp.timestamp() * 1000),
                        'exercise_id': lift.exercise.id,
                        'exercise_name': lift.exercise.name,
                        'workout_session_id': lift.workout_session.id,
                        'lift_mass': lift.lift_mass,
                        'repetitions': lift.repetitions,
                        'one_rep_max': lift.one_rep_max,
                    }
                })
            else:
                return JsonResponse(data={'success': False, 'reason': 'double check workout_session_id and exercise_id'})
        else:
            return JsonResponse(data={'success': False, 'reason': 'double check sessionKey value'})
    else:
        return JsonResponse(data={'success': False, 'reason': f'bad params, must provide {",".join(required_params)}'})
# endregion
