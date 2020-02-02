from django.shortcuts import render, redirect
from django.urls import reverse
from goods.models import GoodsType, IndexGoodsBanner, IndexPromotionBanner, IndexTypeGoodsBanner, GoodsSKU
from order.models import OrderGoods
from django.views.generic import View
from django_redis import get_redis_connection
from django.core.cache import cache
# Create your views here.


# http://127.0.0.1:8080


class IndexView(View):
    """显示首页"""
    def get(self, request):
        # 尝试从缓存中获取数据
        context = cache.get('index_page_data')

        if context is None:
            print('设置缓存')
            # 获取商品的种类信息
            types = GoodsType.objects.all()
            # 获取首页轮播商品信息
            goods_banners = IndexGoodsBanner.objects.all().order_by('index')

            # 获取首页促销活动信息
            promotion_banners = IndexPromotionBanner.objects.all().order_by('index')
            # 获取首页分类商品展示信息
            for type in types:
                # 获取type种类首页分类商品的图片展示信息
                image_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=1)
                title_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=0)

                # 动态给type增加属性，分别保存首页分类商品的图片展示信息和文字展示信息
                type.image_banners = image_banners
                type.title_banners = title_banners

            context = {
                'types': types,
                'goods_banners': goods_banners,
                'promotion_banners': promotion_banners
                }
            # 设置缓存
            # key键 value值 timeout过期时间
            cache.set('index_page_data', context, 3600)

        # 获取用户购物车中商品的数目
        user = request.user
        # 购物车数量默认为0
        cart_count = 0
        if user.is_authenticated:
            # 用户已登录
            conn = get_redis_connection('default')
            cart_key = 'cart_%d'%user.id
            cart_count = conn.hlen(cart_key)
            # 组织上下文
            # 更新用户购物车中的商品数量
        context.update(cart_count=cart_count)
            # print(type(context))
        # 使用
        return render(request, 'index.html', context)


# /goods/商品id
class DetailView(View):
    """详情页"""
    def get(self, request, goods_id):
        """显示详情页"""
        try:
            sku = GoodsSKU.objects.get(id=goods_id)
        except GoodsSKU.DoesNotExist:
            # 商品不存在
            # 返回首页
            return redirect(reverse('good:index'))

        # 获取商品的分类信息
        types = GoodsType.objects.all()

        # 获取商品的评论信息
        sku_orders = OrderGoods.objects.filter(sku=sku).exclude(comment='') # 移除评论为空的结果

        # 获取新品信息
        new_skus = GoodsSKU.objects.filter(type=sku.type).order_by('-create_time')  # 新品列表降序

        # 获取用户购物车中商品的数目
        user = request.user
        # 购物车数量默认为0
        cart_count = 0
        if user.is_authenticated:
            # 用户已登录
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id
            cart_count = conn.hlen(cart_key)

        # 组织模板上下文
        context = {'sku': sku, 'types': types,
                   'sku_orders': sku_orders, 'new_skus': new_skus,
                   'cart_count': cart_count}
        
        return render(request, 'detail.html', context)