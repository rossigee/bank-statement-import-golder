======================
Bank Statements update
======================

Overview
========

Overrides bank statement import logic to create a new statement if one doesn't already exist, or to add missing transactions to an existing statement if one exists. This allows me to import and begin reconciling a downloaded bank statement half way through the month, and import more recent ones later in the month without having to delete an existing statement or create a new one.

NOTE: Depends on (and forces) statement names to be the month of the statement in YYYY-MM format.


Credits
=======

Authors
~~~~~~~

* Ross Golder <ross@golder.org>
