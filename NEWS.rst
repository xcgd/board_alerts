=======
History
=======

13.0.1.0.0
----------

* Migrate to Odoo 13.0.

11.0.1.0.0
----------

* Migrate to Odoo 11.0.

.. _10.0.1.7:

10.0.1.7
~~~~~~~~

- Port to Odoo 10.


.. _8.0.1.7:

8.0.1.7
~~~~~~~

- Change field name in the alert email.template (changed in odoo 8.0)


Version 1.5
~~~~~~~~~~~

* Only users in the base "employee" group can see boards, so only they can receive board alerts.


Version 1.4
~~~~~~~~~~~

* Content formatting.


board_alerts 1.3
~~~~~~~~~~~~~~~~

* [TKT/2015/01414] Fix issue with user language not used correctly on default alert mail template

board_alerts 1.2
~~~~~~~~~~~~~~~~

Production release

board_alerts 1.1.1
~~~~~~~~~~~~~~~~~~

* The board alert email template is now defined on "user" objects instead of "board" objects.
This makes the email template more regular; in particular, the "preview" feature works.

Update note: Delete the board alert email template and the board alert cron task before updating.


board_alerts 1.1
~~~~~~~~~~~~~~~~ 

Production release


Version 1.0.2
~~~~~~~~~~~~~

* Avoid sending empty tables in alert emails.
