import re
from user.models import User
from django.shortcuts import render, redirect
from django.views.generic import View
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer


# Create your views here.


# /user/register
from django.urls import reverse


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



        # 返回应答，跳转到首页
        return redirect(reverse('goods:index'))
