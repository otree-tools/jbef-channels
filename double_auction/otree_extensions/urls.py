from django.conf.urls import url, include

from double_auction.views import AskList, BidList, ContractList

views_to_add = [AskList, BidList, ContractList]
urlpatterns = [url(i.url_pattern, i.as_view(), name=i.url_name) for i in views_to_add]
