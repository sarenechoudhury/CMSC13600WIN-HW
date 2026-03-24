from django.http import HttpResponse, HttpResponseBadRequest
from datetime import datetime, timezone, timedelta
from decimal import Decimal, InvalidOperation

CST = timezone(timedelta(hours=-6))  # fixed Central Standard Time (UTC-6)

def time_endpoint(request):
    if request.method != "GET":
        return HttpResponseBadRequest("GET only")
    now_cst = datetime.now(timezone.utc).astimezone(CST)
    return HttpResponse(now_cst.strftime("%H:%M"))

def sum_endpoint(request):
    if request.method != "GET":
        return HttpResponseBadRequest("GET only")

    n1 = request.GET.get("n1")
    n2 = request.GET.get("n2")
    if n1 is None or n2 is None:
        return HttpResponseBadRequest("Missing n1 or n2")

    try:
        total = Decimal(n1) + Decimal(n2)
    except InvalidOperation:
        return HttpResponseBadRequest("n1 and n2 must be numbers")

    return HttpResponse(str(total))


