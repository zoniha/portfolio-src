from django.shortcuts import render
from django.shortcuts import render, redirect
from django.template import loader
from django.views import generic
from django.urls import reverse_lazy
from django.http import HttpResponse
from django.core.mail import send_mail, EmailMessage, BadHeaderError
from django.conf import settings
from .forms import PhotoForm
from .models import Photo
from django.conf import settings


class IndexView(generic.TemplateView):
    template_name = 'afterglow/index.html'


class AfterglowDet(generic.FormView):
    template_name = 'afterglow/ag_det.html'
    form_class = PhotoForm
    success_url = reverse_lazy('afterglow:afterglow_det')


class ResultView(generic.View):

    def post(self, request):
        form = PhotoForm(request.POST, request.FILES)
        if not form.is_valid():
            return redirect('afterglow:input_error')

        photo = Photo(image=form.cleaned_data['image'])
        image = photo.detect_main()
        template = loader.get_template('afterglow/result.html')


        context = {
            'photo_name':photo.image.name,
            'photo_data':image,
        }

        return HttpResponse(template.render(context, request))


class InputErrorView(generic.TemplateView):
    template_name = 'afterglow/input_error.html'


class MyProfileView(generic.TemplateView):
    template_name = 'afterglow/my_profile.html'
