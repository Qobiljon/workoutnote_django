from django.shortcuts import render


def handle_index(request):
    return render(request=request, template_name='index/index.html')


def handle_calculators(request):
    return render(request=request, template_name='index/calculators.html')


def handle_strength_standards(request):
    return render(request=request, template_name='index/strength standards.html')


def handle_training_log_tutorial(request):
    return render(request=request, template_name='index/training log tutorial.html')


def handle_login(request):
    return render(request=request, template_name='index/sub html authentication.html')


def handle_one_rep_max_calculator(request):
    return render(request=request, template_name='index/one rep max calculator.html')


def handle_plate_barbell_racking_calculator(request):
    return render(request=request, template_name='index/plate barbell racking calculator.html')


def handle_powerlifting_calculator(request):
    return render(request=request, template_name='index/powerlifting calculator.html')


def handle_wilks_calculator(request):
    return render(request=request, template_name='index/wilks calculator.html')