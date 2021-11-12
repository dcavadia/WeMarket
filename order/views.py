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

            #API REQUEST
            response_data = {}
            response_data['numero'] = form.cleaned_data['ccnumber']
            response_data['ccv'] = form.cleaned_data['secnumber']
            response_data['monto'] = int(total)

            mytoken = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiI5NGJmYzk0MS0zZjllLTQ3YWItYjBhNS05Y2Q0OWNjYzhlZDkiLCJqdGkiOiIxNTg4MTIyNGVkMjM2MmNjNzNmNDM0NTYxNWE2NDBlYjdkMmRiY2ZhZjBhYjUxYWM0MmQyM2E4NTUwYWNmYWE3NjlkYzg1NDgyNTQ1ODBhMCIsImlhdCI6MTYzNjY3NTM4Ni45ODExNzYsIm5iZiI6MTYzNjY3NTM4Ni45ODExOCwiZXhwIjoxNjY4MjExMzg2Ljk3MDg2OCwic3ViIjoiMTgiLCJzY29wZXMiOltdfQ.pV2_UlePrk3Gja37mbv17b71Ad15OaOZXT_ZcT-ZtV6FFhxyeL2a09d2rWdNweWPZkcd1joT5zltFb_rU57IoHXWTVVUT-pJn4AodHnTbqhBulZK9nLi3mqyPJrUSiH-QzjCPpKPrv_vL9FXdrVv0HHt0tS-I1CUJ52cPLReSKZKE92kASExO1SIGBlZsrWhLr5EhSbmpJYTp8ojYphWiTEu7QDDybvSN23dX3sZjGiWMDVSVnTqVH-RMZLG3hGskzGArGFi0YicIJvKV00xLaqq6RbpnqFTTT_apEUxGRlMu0XIImEBtBMf1pV7NuYQP-wpnmLFo3GESHRONad8KOfPep6dXm7s-kk3IGs2hL5sW0WxDd_KixXxWZniZOqDMFgRQoCEoK6UpN7JuJuj0yqP2B1hoC0Ln3ZscmJo3UUtnrYquIpEgrL3sgHhjv1DJvfTxq9riUO_TBIYFxbr8DNUz6o6wM22_AikfaXP5wThAVwnlSu6zlbuXsKZVhmUY-L4rvRLjnxPVtR_oX6NCV-7m_VNQAMwXcd6bhss1i1qenDQt0ocmgAF1acinre5D_m62Z-mAIzS51Kw8LxTzu9FO8AKljqZxiefcbg39f36dVguJaMpQ2WEsJYFKILIvd_Tpjaf5dAmy0TYUrv481lkyKWT9TBg0Ztvz1R5Pnw"
            url = "https://punibank.herokuapp.com/public/api/payment/pay"

            headers = {
              'Authorization': 'Bearer {}'.format(mytoken),
              'Content-Type': 'application/json'
            }
            print(json.dumps(headers))
            print(json.dumps(response_data, cls=DecimalEncoder))
            # Enviar tarjeta de credito a banco, si el banco responde ok, continuar, si no , mostrar el error
            r = requests.request("POST", url, headers=headers, data=json.dumps(response_data, cls=DecimalEncoder))

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
                #return render(request, 'Order_Failed.html',{'category': category})
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