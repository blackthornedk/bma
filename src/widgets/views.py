from django.shortcuts import render

def bma_widget(request, style, count, uuid):
    return render(request, f'{style}.js', context={"uuid": uuid, "count": count, "host": request.get_host()}, content_type='text/javascript')
