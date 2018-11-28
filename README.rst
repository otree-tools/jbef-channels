=====
Real time interactions in oTree using Django Channels
=====
Auctions and real effort tasks
--------


This code contains four applications to use in oTree [Chen2016]_.

The demo app based on this code is available at Heroku_.


1. :code:`minimum`: a bare  example how to use Django Channels in oTree projects
to build a very simple real effort task (subtracting random number from X).


2.:code:`realefforttask`: a set of four different real effort tasks:

-  summing up *N* numbers [Niederle2007]_.
- finding max of two matrices [Schram2017]_.
- decoding task [Erkal2011]_.
- counting 0s in a matrix [Abeler2011]_.

This app also provides a platform for development one's own tasks using
TaskGenerator class from `ret_functions` module located in `realefforttask` app folder.
To use it, create a child of `TaskGenerator` class in `ret_functions` module, and reference it
in `settings.py` configuration for your app.


3. :code:`auctionone` -  a gift-exchange game [Fehr1993]_ where employers hire workers in the
open auction, and workers reciprocate their salary in a subsequent real effort task stage.

4. :code:`double_auction` -  a trading platform where buyers and sellers can
trade their goods by posting bids (for buyers) and asks (for sellers) [Smith1962]_.



References
--------
.. _Heroku: https://jbef-channels.herokuapp.com/
.. [Chen2016] Chen, D. L., Schonger, M., & Wickens, C. (2016). oTree—An open-source platform for laboratory, online, and field experiments. Journal of Behavioral and Experimental Finance, 9, 88-97.
.. [Niederle2007] Niederle, M., & Vesterlund, L. (2007). Do women shy away from competition? Do men compete too much?. The quarterly journal of economics, 122(3), 1067-1101.
.. [Schram2017] Weber, M., & Schram, A. (2017). The Non‐equivalence of Labour Market Taxes: A Real‐effort Experiment. The Economic Journal, 127(604), 2187-2215.
.. [Erkal2011] Erkal, N., Gangadharan, L., & Nikiforakis, N. (2011). Relative earnings and giving in a real-effort experiment. American Economic Review, 101(7), 3330-48.
.. [Abeler2011] Abeler, J., Falk, A., Goette, L., & Huffman, D. (2011). Reference points and effort provision. American Economic Review, 101(2), 470-92.
.. [Fehr1993] Fehr, E., Kirchsteiger, G., & Riedl, A. (1993). Does fairness prevent market clearing? An experimental investigation. The quarterly journal of economics, 108(2), 437-459.
.. [Smith1962] Smith, V. L. (1962). An experimental study of competitive market behavior. Journal of political economy, 70(2), 111-137.