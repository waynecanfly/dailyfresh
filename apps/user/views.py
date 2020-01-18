import re

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django_redis import get_redis_connection
from user.models import User, Address
from goods.models import GoodsSKU
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.views.generic import View
from django.conf import settings
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired
from django.core.mail import send_mail
from utils.mixin import LoginRequiredMixin


# Create your views here.


# /user/register
from django.urls import reverse

from celery_tasks.tasks import send_register_active_email


def register(request):
    """显示注册页面"""
    return render(request, 'register.html')


def register_handle(request):
    """进行用户注册"""

    # 接收数据
    username = request.POST.get('user_name')
    password = request.POST.get('pwd')
    email = request.POST.get('email')
    # 进行数据校验
    if not all([username, password, email]):
        # 数据不完整
        return render(request, 'register.html', {'errmsg': '数据不完整'})


    # 校验邮箱
    if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
        return render(request, 'register.html', {'errmsg': '邮箱格式不正确'})

    # 进行业务处理：进行用户注册
    user = User.objects.create_user(username, email, password)

    # 返回应答，跳转到首页
    return redirect(reverse('goods:index'))


class RegisterView(View):

    def get(self, request):
        return render(request, 'register.html')

    def post(self, request):
        """进行用户注册"""

        # 接收数据
        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        email = request.POST.get('email')
        # 进行数据校验
        if not all([username, password, email]):
            # 数据不完整
            return render(request, 'register.html', {'errmsg': '数据不完整'})

        # 校验邮箱
        if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'register.html', {'errmsg': '邮箱格式不正确'})

        # 进行业务处理：进行用户注册
        user = User.objects.create_user(username, email, password)
        user.is_active = 0 # 默认是未激活状态
        user.save()

        # 发送激活邮件，包含激活链接： 127.0.0.1:8000/user/active/3
        # 使用token对包含用户的身份信息进行加密
        serializer = Serializer(settings.SECRET_KEY, expires_in=3600)
        info = {'confirm': user.id}
        token = serializer.dumps(info)
        token = token.decode()
        # 发送激活邮件
        # subject 主题
        send_register_active_email.delay(email, username, token)

        # 返回应答，跳转到首页
        return redirect(reverse('goods:index'))


class ActiveView(View):
    """用户激活"""

    def get(self, request, token):
        # token揭密，获取用户信息
        serializer = Serializer(settings.SECRET_KEY, expires_in=3600)
        try:
            print(token)
            info = serializer.loads(token)
            user_id = info['confirm']

            # 根据id更改数据库胡is_active
            user = User.objects.get(id=user_id)
            user.is_active = 1
            user.save()

            # 跳转登录页面
            return redirect(reverse('user:login'))

        except SignatureExpired as e:
            # 激活链接一过期
            return HttpResponse('激活链接已经过期')


# /user/login
class LoginView(View):
    """登录页面"""
    def get(self, request):
        """显示登陆页面"""
        # 判断是否记住用户名
        if 'username' in request.COOKIES:
            username = request.COOKIES.get('username')
            checked = 'checked'

        else:
            username = ''
            checked = ''

        return render(request, 'login.html', {'username': username, 'checked': checked})

    def post(self, request):
        """进行登陆处理"""
        username = request.POST.get('username')
        password = request.POST.get('pwd')

        # 数据校验
        if not all([username, password]):
            return render(request, 'login.html', {'errmsg': '数据不完整'})
        # 用户认证
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                # 用户已激活
                # 记录用户登陆状态
                login(request, user)

                # 获取登陆后要跳转的地址
                next_url = request.GET.get('next', reverse('goods:index'))

                # 跳转到首页
                response = redirect(next_url)
                # 判断是否需要记住用户名
                remember = request.POST.get('remember')
                
                if remember == 'on':
                    # 记住用户名
                    response.set_cookie('username', username, max_age=7*24*3600)
                else:
                    response.delete_cookie('username')

                return response
            else:
                # 用户未激活
                return render(request, 'login.html', {'errmsg': '账户未激活'})
        else:
            return render(request, 'login.html', {'errmsg': '用户名或密码错误'})

# /user/logout
class LogoutView(View):
    def get(self, request):
        # 清除用户session信息
        logout(request)
        return redirect(reverse('goods:index'))



# /user
class UserInfoView(LoginRequiredMixin, View):
    """用户中心-信息页"""
    def get(self, request):
        # page = 'user'
        # django会给request对象添加一个属性request.user
        # 如果用户未登录->user是anonymousUser类的一个实例
        # 如果用户登录->user是User类的一个实例
        # 获取用户的个人信息
        user = request.user
        address = Address.objects.get_default_address(user)

        # 获取用户的历史浏览记录
        con = get_redis_connection('default')

        history_key = 'history_%d'%user.id

        # 获取用户最新浏览的五个商品id
        sku_ids = con.lrange(history_key, 0, 4) # [2,3,1]

        # 从数据库中查询用户浏览的商品的具体信息
        # goods_li = GoodsSKU.objects.filter(id__in=sku_ids)

        # 遍历获取用户浏览的历史商品信息
        goods_li = []
        for id in sku_ids:
            goods = GoodsSKU.objects.get(id=id)
            goods_li.append(goods)

        # 组织上下文
        context = {'page': 'user',
                   'address': address,
                   'goods_li': goods_li}

        return render(request, 'user_center_info.html', context)


# /user/order
class UserOrderView(LoginRequiredMixin, View):
    """用户中心-订单页"""
    def get(self, request):
        # page = 'order'
        return render(request, 'user_center_order.html', {'page': 'order'})


# /user/address
class AddressView(LoginRequiredMixin, View):
    """用户中心-地址页"""
    def get(self, request):
        # page = 'address'
        # 获取用户默认收货地址
        user = request.user

        # try:
        #     address = Address.objects.get(user=user, is_default=True)
        # except Address.DoesNotExist:
        #     # 不存在默认地址
        #     address = None

        address = Address.objects.get_default_address(user)

        return render(request, 'user_center_site.html', {'page': 'address', 'address': address})

    def post(self,request):
        # 接收数据
        receiver = request.POST.get('receiver')
        addr = request.POST.get('addr')
        zip_code = request.POST.get('zip_code')
        phone = request.POST.get('phone')

        # 校验数据
        if not all([receiver, addr, phone]):
            return render(request, 'user_center_site.html', {'errmsg': '数据不完整'})

        # 校验手机号
        if not re.match(r'^1[35678]\d{9}$', phone):
            return render(request, 'user_center_site.html', {'errmsg': '数据格式不正确'})

        # 业务处理:地址添加
        # 如果用户已存在默认收货地址，添加的地址不作为默认收货地址，否则作为默认收货地址
        # 获取登录用户对应的User对象
        user = request.user

        # try:
        #     address = Address.objects.get(user=user, is_default=True)
        # except Address.DoesNotExist:
        #     # 不存在默认地址
        #     address = None
        address = Address.objects.get_default_address(user)

        if address:
            is_default = False
        else:
            is_default = True
        # 添加地址
        Address.objects.create(user=user,
                               receiver=receiver,
                               addr=addr,
                               zip_code=zip_code,
                               phone=phone,
                               is_default=is_default)
        # 返回应答
        return redirect(reverse('user:address')) # get请求方式
