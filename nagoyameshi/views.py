from django.shortcuts import render, redirect

# Create your views here.

from django.views.generic import TemplateView, DetailView, ListView, UpdateView
from .models import Restaurant, Review, Favorite, Reservation, PremiumUser, Category

# スペース区切りの検索に対応するためのクエリビルダ
from django.db.models import Q, Sum

import datetime
from django.utils import timezone

from .forms import UserForm

class TopView(TemplateView):
    template_name = "nagoyameshi/top.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["categories"] = Category.objects.all() 

        query = Q()

        print(self.request.GET)
        # 検索フォームに入力されたキーワード取得
        # 事前にキーワードがあるかチェック
        if "search" in self.request.GET:
            # context['restaurants'] = Restaurant.objects.filter(name=self.request.GET["search"])←完全一致の場合

            # 指定したキーワードを含む検索にする。 __icontains : 指定したキーワードを含む( 英字の場合大文字と小文字の区別はしない)
            #  __icontains : 指定したキーワードを含む( 英字の場合大文字と小文字の区別はしない)、__contains : 指定したキーワードを含む( 英字の場合大文字と小文字の区別はする)
            #context['restaurants'] = Restaurant.objects.filter(name__icontains=self.request.GET["search"])

            # スペース区切りの検索に対応させるにはクエリビルダを使う。
            # スペース区切りの文字列を、文字列のリスト型に変換する。(全角スペースの場合もある) 
            words = self.request.GET["search"].replace("　"," ").split(" ")

            for word in words:
                query &= Q(name__icontains=word)
            
        """
            # query の wordsのキーワードがすべて条件に含まれた状態になる。
            context['restaurants'] = Restaurant.objects.filter(query)
        else:
            context['restaurants'] = Restaurant.objects.filter(query)
            # ↑は Restaurant.objects.all()と同じ。
        """
        # queryにカテゴリも加える
        if "category" in self.request.GET:
            if self.request.GET["category"] != "":
                query &= Q(category=self.request.GET["category"])

        context['restaurants'] = Restaurant.objects.filter(query)
        return context

class RestaurantDetailView(DetailView):
    model = Restaurant

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 該当店舗のレビューだけ表示
        context["reviews"] = Review.objects.filter(restaurant=kwargs["object"].id)

        context["is_premium"] = PremiumUser.objects.filter(user=self.request.user).exists()

         # ログインをしているのかチェック。
        if self.request.user.is_authenticated:
            # 店舗のお気に入り積みかチェック
            context["is_favorite"] = Favorite.objects.filter(restaurant=kwargs["object"].id, user=self.request.user.id).exists()

        return context

from django.views import View
from .forms import ReviewForm, FavoriteForm, ReservationForm

class ReviewCreateView(View):
    def post(self, request, *args, **kwargs):

        #========有料会員であるかのチェック=======================

        premium_user = PremiumUser.objects.filter(user=request.user).first()

        if not premium_user:
            print("有料会員ではありません。")
            return redirect("mypage")


        # カスタマーIDを元にStripeに問い合わせ
        try:
            subscriptions = stripe.Subscription.list(customer=premium_user.premium_code)
        except:
            print("このカスタマーIDは無効です。")
            premium_user.delete()

            return redirect("mypage")
        
        is_premium = False

        # ステータスがアクティブであるかチェック。
        for subscription in subscriptions.auto_paging_iter():
            if subscription.status == "active":
                print("サブスクリプションは有効です。")
                is_premium = True
            else:
                print("サブスクリプションが無効です。")
            
        if not is_premium:
            premium_user.delete()
            return redirect("mypage")
        
        #========有料会員であるかのチェック=======================


        # POSTメソッド受け取り処理
        form = ReviewForm(request.POST)

        # 投稿されたデータが制約内か検証
        if form.is_valid():
            form.save()
        else:
            print(form.errors)
        
        return redirect("detail", request.POST["restaurant"])

class ReviewUpdateView(UpdateView):
    model = Review
    fields = '__all__'
    template_name_suffix = '_update_form' 

class ReviewCancelView(View):
    def post(self, request, pk, *args, **kwargs):
        # レビューの削除
        review = Review.objects.filter(user=request.user,id=pk)
        review.delete()
        return redirect("mypage")

class FavoriteCreateView(View):
    def post(self, request, *args, **kwargs):

        #========有料会員であるかのチェック=======================

        premium_user = PremiumUser.objects.filter(user=request.user).first()

        if not premium_user:
            print("有料会員ではありません。")
            return redirect("mypage")


        # カスタマーIDを元にStripeに問い合わせ
        try:
            subscriptions = stripe.Subscription.list(customer=premium_user.premium_code)
        except:
            print("このカスタマーIDは無効です。")
            premium_user.delete()

            return redirect("mypage")
        
        is_premium = False

        # ステータスがアクティブであるかチェック。
        for subscription in subscriptions.auto_paging_iter():
            if subscription.status == "active":
                print("サブスクリプションは有効です。")
                is_premium = True
            else:
                print("サブスクリプションが無効です。")
            
        if not is_premium:
            premium_user.delete()
            return redirect("mypage")
        
        #========有料会員であるかのチェック=======================

        #すでに登録済みの場合、削除
        favorites = Favorite.objects.filter(user=request.user, restaurant=request.POST["restaurant"])
        if favorites:
            favorites.delete()
            return redirect("detail", request.POST["restaurant"])

        form = FavoriteForm(request.POST)
        if form.is_valid():
            form.save()
        else:
            print(form.errors)

        return redirect("detail", request.POST["restaurant"])
    
class ReservationCreateView(View):
    def post(self, request, *args, **kwargs):

        #========有料会員であるかのチェック=======================

        premium_user = PremiumUser.objects.filter(user=request.user).first()

        if not premium_user:
            print("有料会員ではありません。")
            return redirect("mypage")


        # カスタマーIDを元にStripeに問い合わせ
        try:
            subscriptions = stripe.Subscription.list(customer=premium_user.premium_code)
        except:
            print("このカスタマーIDは無効です。")
            premium_user.delete()

            return redirect("mypage")
        
        is_premium = False

        # ステータスがアクティブであるかチェック。
        for subscription in subscriptions.auto_paging_iter():
            if subscription.status == "active":
                print("サブスクリプションは有効です。")
                is_premium = True
            else:
                print("サブスクリプションが無効です。")
            
        if not is_premium:
            premium_user.delete()
            return redirect("mypage")
        
        #========有料会員であるかのチェック=======================

        # フローチャート実施
        now = timezone.now()
        form = ReservationForm(request.POST)
        if form.is_valid():
            # 送られてきた全データが型変換されて辞書型で手に入る。
            cleaned = form.clean()

            # datetime型でも比較が出来る
            if now > cleaned["datetime"]:
                print("予約指定した時刻が現在よりも過去になっています")
                return redirect("detail", request.POST["restaurant"])
            
            if cleaned["restaurant"].start_at < cleaned["restaurant"].end_at:
                if cleaned["restaurant"].start_at > cleaned["datetime"].time() or cleaned["datetime"].time() > cleaned["restaurant"].end_at:
                    print("予約指定した時刻が営業時間外です")
                    return redirect("detail", request.POST["restaurant"])
            else:
                if cleaned["restaurant"].end_at < cleaned["datetime"].time() < cleaned["restaurant"].start_at:
                    print("予約指定した時刻が営業時間外です")
                    return redirect("detail", request.POST["restaurant"])
            
            # 指定した人数が収容できるか分岐する。
            if cleaned["restaurant"].capacity < cleaned["headcount"]:
                print("店舗の収容人数を超えています")
                return redirect("detail", request.POST["restaurant"])
            
            # +-30分で同じ店舗に予約されているか調べる
            reservation_start_time = cleaned["datetime"] - datetime.timedelta(minutes=30)
            reservation_end_time = cleaned["datetime"] + datetime.timedelta(minutes=30)

            data = Reservation.objects.filter(datetime__gte=reservation_start_time, datetime__lte=reservation_end_time, restaurant=cleaned["restaurant"]).aggregate(Sum("headcount"))
            print(data)
            print(data["headcount__sum"])

            if data["headcount__sum"] == None:
                data["headcount__sum"] = 0
            if cleaned["restaurant"].capacity < cleaned["headcount"] + data["headcount__sum"]:
                print("予約できる人数を超過しています")
                return redirect("detail", request.POST["restaurant"])

            form.save()
        else:
            print(form.errors)
        return redirect("detail", request.POST["restaurant"])
    
class MypageView(TemplateView):
    template_name = "nagoyameshi/mypage.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["is_premium"] = PremiumUser.objects.filter(user=self.request.user).exists()

        return context
    
class MypageUpdateView(View):
    def get(self, request, *args, **kwargs):
        return render(request, "nagoyameshi/mypage_update.html")

    def post(self, request, *args, **kwargs):
        # 編集を受け付ける
        form = UserForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
        else:
            print(form.error)
        
        return redirect("mypage")

class FavoriteListView(ListView):
    model = Favorite
    template_name = "nagoyamehi/favorite_list.html"

    # 他のユーザーの分が反映しないように
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object_list"] = Favorite.objects.filter(user=self.request.user)
        return context
    

class ReservationListView(ListView):
    model = Reservation
    template_name = "nagoyameshi/reservation_list.html"

    # 他のユーザーの分が反映しないように
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object_list"] = Reservation.objects.filter(user=self.request.user)
        return context
    
class ReservationCancelView(View):
    def post(self, request, pk, *args, **kwargs):
        # 予約のキャンセル
        reservation = Reservation.objects.filter(id=pk, user=request.user)

        # TODO: 必要があればif文で更に絞り込み(例:予約キャンセル不可の時間になった場合はキャンセルしない。)
        reservation.delete()
        return redirect("mypage")

# サブスク登録はログイン済みのユーザーだけ
from django.contrib.auth.mixins import LoginRequiredMixin
# setting.pyの内容を用意
from django.conf import settings
# リダイレクト先の指定（カード決済を終えた後のリダイレクト先の指定）
from django.urls import reverse_lazy
# stripe ライブラリをimport , pip install stripe
import stripe

# セッションを作るため、APIキーをセット
stripe.api_key  = settings.STRIPE_API_KEY

# 「有料会員登録をする」ボタン　CheckoutViewのpostメソッドへ
"""
class IndexView(LoginRequiredMixin,View):
    def get(self, request, *args, **kwargs):
        return render(request, "bbs/index.html")

index   = IndexView.as_view()
"""

# 1~4: セッションを作って、ユーザーがカード入力ページへ
class CheckoutView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):

        # 1: セッションを作る
        checkout_session = stripe.checkout.Session.create(
            line_items=[
                {
                    'price': settings.STRIPE_PRICE_ID,
                    'quantity': 1,
                },
            ],
            payment_method_types=['card'],
            mode='subscription',
            # カード決済が失敗、成功したときのダイレクト先を指定
            # TIPS: Stripeからのリダイレクトなため、https://~から始まるように
            success_url=request.build_absolute_uri(reverse_lazy("success")) + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.build_absolute_uri(reverse_lazy("mypage")),
        )

        # 2: セッションid
        print( checkout_session["id"] )

        # 3~4: リダイレクト　～　ユーザーがカードの入力
        return redirect(checkout_session.url)

# 7: セッションidを使ってstripeに決済をしたか確認
class SuccessView(LoginRequiredMixin,View):
    def get(self, request, *args, **kwargs):

        # パラメータにセッションIDがあるかチェック
        if "session_id" not in request.GET:
            print("セッションIDがありません。")
            return redirect("top")


        # そのセッションIDは有効であるかチェック。
        try:
            checkout_session_id = request.GET['session_id']
            checkout_session    = stripe.checkout.Session.retrieve(checkout_session_id)
        except:
            print( "このセッションIDは無効です。")
            return redirect("top")

        print(checkout_session)

        # statusをチェックする。未払であれば拒否する。(未払いのsession_idを入れられたときの対策)
        if checkout_session["payment_status"] != "paid":
            print("未払い")
            return redirect("top")

        print("支払い済み")


        # 有効であれば、セッションIDからカスタマーIDを取得。ユーザーモデルへカスタマーIDを記録する。
        """
        request.user.customer   = checkout_session["customer"]
        request.user.save()
        """

        premium_user = PremiumUser()    
        premium_user.user = request.user
        premium_user.premium_code = checkout_session["customer"]
        premium_user.save()

        print("有料会員登録しました！")

        return redirect("mypage")

# サブスクリプションの操作関係
class PortalView(LoginRequiredMixin,View):
    def get(self, request, *args, **kwargs):

        premium_user = PremiumUser.objects.filter(user=request.user).first()

        if not premium_user:
            print( "有料会員登録されていません")
            return redirect("mypage")

        # ユーザーモデルに記録しているカスタマーIDを使って、ポータルサイトへリダイレクト
        portalSession   = stripe.billing_portal.Session.create(
            customer    = premium_user.premium_code ,
            return_url  = request.build_absolute_uri(reverse_lazy("mypage")),
        )

        return redirect(portalSession.url)

class PremiumView(View):
    def get(self, request, *args, **kwargs):
        
        premium_user = PremiumUser.objects.filter(user=request.user).first()

        if not premium_user:
            print("有料会員ではありません。")
            return redirect("mypage")


        # カスタマーIDを元にStripeに問い合わせ
        try:
            subscriptions = stripe.Subscription.list(customer=premium_user.premium_code)
        except:
            print("このカスタマーIDは無効です。")
            premium_user.delete()

            return redirect("mypage")
        
        is_premium = False

        # ステータスがアクティブであるかチェック。
        for subscription in subscriptions.auto_paging_iter():
            if subscription.status == "active":
                print("サブスクリプションは有効です。")
                is_premium = True
            else:
                print("サブスクリプションが無効です。")
            
        if not is_premium:
            premium_user.delete()
            return redirect("mypage")
        
        # 有料会員向けの処理を実行する。
        return redirect("")

premium     = PremiumView.as_view()