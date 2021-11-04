from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render

# Create your views here.
from django.utils.crypto import get_random_string

from order.models import ShopCart, ShopCartForm, OrderForm, Order, OrderProduct
from product.models import Category, Product, Variants
from user.models import UserProfile

from decimal import Decimal

import json
import requests


def index(request):
    return HttpResponse ("Order Page")

@login_required(login_url='/login') # Check login
def addtoshopcart(request,id):
    url = request.META.get('HTTP_REFERER')  # get last url
    current_user = request.user  # Access User Session information
    product= Product.objects.get(pk=id)

    if product.variant != 'None':
        variantid = request.POST.get('variantid')  # from variant add to cart
        checkinvariant = ShopCart.objects.filter(variant_id=variantid, user_id=current_user.id)  # Check product in shopcart
        if checkinvariant:
            control = 1 # The product is in the cart
        else:
            control = 0 # The product is not in the cart"""
    else:
        checkinproduct = ShopCart.objects.filter(product_id=id, user_id=current_user.id) # Check product in shopcart
        if checkinproduct:
            control = 1 # The product is in the cart
        else:
            control = 0 # The product is not in the cart"""

    if request.method == 'POST':  # if there is a post
        form = ShopCartForm(request.POST)
        if form.is_valid():
            if control==1: # Update  shopcart
                if product.variant == 'None':
                    data = ShopCart.objects.get(product_id=id, user_id=current_user.id)
                else:
                    data = ShopCart.objects.get(product_id=id, variant_id=variantid, user_id=current_user.id)
                data.quantity += form.cleaned_data['quantity']
                data.save()  # save data
            else : # Inser to Shopcart
                data = ShopCart()
                data.user_id = current_user.id
                data.product_id =id
                data.variant_id = variantid
                data.quantity = form.cleaned_data['quantity']
                data.save()
        messages.success(request, "Product added to Shopcart ")
        return HttpResponseRedirect(url)

    else: # if there is no post
        if control == 1:  # Update  shopcart
            data = ShopCart.objects.get(product_id=id, user_id=current_user.id)
            data.quantity += 1
            data.save()  #
        else:  #  Inser to Shopcart
            data = ShopCart()  # model ile bağlantı kur
            data.user_id = current_user.id
            data.product_id = id
            data.quantity = 1
            data.variant_id =None
            data.save()  #
        messages.success(request, "Product added to Shopcart")
        return HttpResponseRedirect(url)


def shopcart(request):
    category = Category.objects.all()
    current_user = request.user  # Access User Session information
    shopcart = ShopCart.objects.filter(user_id=current_user.id)
    total=0
    for rs in shopcart:
        total += rs.product.price * rs.quantity
    #return HttpResponse(str(total))
    context={'shopcart': shopcart,
             'category':category,
             'total': total,
             }
    return render(request,'shopcart_products.html',context)

@login_required(login_url='/login') # Check login
def deletefromcart(request,id):
    ShopCart.objects.filter(id=id).delete()
    messages.success(request, "Your item deleted form Shopcart.")
    return HttpResponseRedirect("/shopcart")

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return json.JSONEncoder.default(self, obj)


def orderproduct(request):
    category = Category.objects.all()
    current_user = request.user
    shopcart = ShopCart.objects.filter(user_id=current_user.id)
    total = 0
    for rs in shopcart:
        if rs.product.variant == 'None':
            total += rs.product.price * rs.quantity
        else:
            total += rs.variant.price * rs.quantity

    if request.method == 'POST':
        form = OrderForm(request.POST)
        #return HttpResponse(request.POST.items())
        if form.is_valid():

            data = Order()
            data.first_name = form.cleaned_data['first_name'] #get product quantity from form
            data.last_name = form.cleaned_data['last_name']
            data.address = form.cleaned_data['address']
            data.city = form.cleaned_data['city']
            data.phone = form.cleaned_data['phone']
            data.ccnumber = form.cleaned_data['ccnumber']
            data.secnumber = form.cleaned_data['secnumber']
            data.user_id = current_user.id
            data.total = total
            data.ip = request.META.get('REMOTE_ADDR')
            ordercode= get_random_string(5).upper() # random cod
            data.code =  ordercode
            data.save() #

            response_data = {}
            response_data['numero'] = form.cleaned_data['ccnumber']
            response_data['ccv'] = form.cleaned_data['secnumber']
            response_data['monto'] = int(total)

            mytoken = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiI5NGJmYzk0MS0zZjllLTQ3YWItYjBhNS05Y2Q0OWNjYzhlZDkiLCJqdGkiOiJiZWZhMzU1NDBlM2JmOGJiYWJlNjY1ZWUyZmNmOTNmMzJlMGJiYjEwNTkzNTUzZTU0ZWVhNzY1NWJjNjBjNzljM2I4MDhhZGMwNzY0Y2JjYSIsImlhdCI6MTYzNTc4MDU3Mi41MDU2MjMsIm5iZiI6MTYzNTc4MDU3Mi41MDU2MjcsImV4cCI6MTY2NzMxNjU3Mi41MDA1NTMsInN1YiI6IjE1Iiwic2NvcGVzIjpbXX0.WqdFkin3ABPT9ZJbYQEnG66tEMLphx3tB9x6PQljSMUR8CuIRyqZcWLVh0ya1cTbUmPGrNkwn5t7hNCgaWDXVsEAVO3Td7UejPF0ArxVm0_DXQ1NMLF4gvit0TJHlEHJamCMU_yo8V9pAKsSy6t5dGsf1m9Js6tL5Imz_2My_Ka-KhkLsNWn5oPUtjhrcXomVHJve6RbItI4cxQyk0SGvLX95b26U0jGmtlq7YhMAp1DvePX2_PFbMYJq1n6VogtUYY4G6wFRLNiatotkLZrb6M6HI2Y6f3_cA1iL3khKW9P9EttYSb1cHrfTzXSr7Vz467PxtU5dtHRSVGVmMgn4eOK3cDu454F0Rpoo-sI09nRwPbVtqJ4v7smhdlqUy5khow0PThuKnZxpndI36ACRyN0k_gEIO1oWjiV6Oyq8eFfcKSV07lJ43SqCIy-Rh9HoGARoC6IDH7MMO4lWDRrm_TECgfcDfZ-3a-OiePO-IT9P450YFTG5Z0ZhKktDiJXQWbtoV2pd43xJHH-ynCRkle-312jgVhPm0Uy4cxdPB7shMS_rS2YD4QL2FlY6ibE6LvopK8QL6cIoiGw7WLmYN8gHv2RJibJKXJk1i563GTj1itEa-MZLvVW05hozrXuARNJ8m6uz37z3u2zhNnInk6a1msIDlL-LfkdXYCzJ1s"
            url = "https://punibank.herokuapp.com/public/api/payment/pay"

            headers = {
              'Authorization': 'Token {}'.format(mytoken),
            }

            print(json.dumps(response_data, cls=DecimalEncoder))
            r = requests.request("POST", url, headers=headers, data=json.dumps(response_data, cls=DecimalEncoder))

            # Enviar tarjeta de credito a banco, si el banco responde ok, continuar, si no , mostrar el error
            #r = requests.post(myurl, data=content, headers={'Authorization': 'Token {}'.format(mytoken)})

            # Tarjet paso
            if r.status_code == 200:
                print(f'Post succeed: {r}')
                


                for rs in shopcart:
                    detail = OrderProduct()
                    detail.order_id     = data.id # Order Id
                    detail.product_id   = rs.product_id
                    detail.user_id      = current_user.id
                    detail.quantity     = rs.quantity
                    if rs.product.variant == 'None':
                        detail.price    = rs.product.price
                    else:
                        detail.price = rs.variant.price
                    detail.variant_id   = rs.variant_id
                    detail.amount        = rs.amount
                    detail.save()
                    # ***Reduce quantity of sold product from Amount of Product
                    if  rs.product.variant=='None':
                        product = Product.objects.get(id=rs.product_id)
                        product.amount -= rs.quantity
                        product.save()
                    else:
                        variant = Variants.objects.get(id=rs.product_id)
                        variant.quantity -= rs.quantity
                        variant.save()
                    #************ <> *****************

                ShopCart.objects.filter(user_id=current_user.id).delete() # Clear & Delete shopcart
                request.session['cart_items']=0
                messages.success(request, "Your Order has been completed. Thank you ")
                return render(request, 'Order_Completed.html',{'ordercode':ordercode,'category': category})
            #Tarjeta no paso
            else:
                print(f'Post failed: {r}')        
        else:
            messages.warning(request, form.errors)
            return HttpResponseRedirect("/order/orderproduct")

    form= OrderForm()
    profile = UserProfile.objects.get(user_id=current_user.id)
    context = {'shopcart': shopcart,
               'category': category,
               'total': total,
               'form': form,
               'profile': profile,
               }
    return render(request, 'Order_Form.html', context)