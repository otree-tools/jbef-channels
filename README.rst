=====
Real time interactions in oTree using Django Channels
=====
Auctions and real effort tasks
--------


This code contains four applications to use in oTree [Chen2016]_.

The demo app based on this code is available at Heroku_.

1. `minimum`: a bare  example how to use Django Channels in oTree projects
to build a very simple real effort task (subtracting random number from X).

2. `realefforttask`: a set of four different real effort tasks:
    -  summing up _N_ numbers
    - finding max of two matrices
    - decoding task
    - counting 0s in a matrix
    This app also provides a platform for development one's own tasks using
    TaskGenerator class from `ret_functions` module located in `realefforttask` app folder.

3. `auctionone` -  a gift-exchange game where employers hire workers in the
open auction, and workers reciprocate their salary in a subsequent real effort task stage.

4. `double_auction` -  a trading platform where buyers and sellers can
trade their goods by posting bids (for buyers) and asks (for sellers).



References
--------
.. _Heroku: https://jbef-channels.herokuapp.com/

.. [Chen2016] Chen, D. L., Schonger, M., & Wickens, C. (2016). oTree—An open-source platform for laboratory, online, and field experiments. Journal of Behavioral and Experimental Finance, 9, 88-97.