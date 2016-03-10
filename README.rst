Kjosa is 'vote' in Icelandic -- or at least that's what googling says.

This is a framework to allow sms voting (and possibly an api from an app)
securely regularly, robustly and easily.

Secure means:

* There is a protocol for someone to send a vote without their phone
  company or other intermediate-third party knowing their vote
* The server itself cannot map a vote to a particular citizen
* Users should be able to verify that their vote was counted

We also want the following goals:
* People should be able to change their phone numbers securely without
  a full visit to an administration station (polling/DMV/etc)
* People should NOT be able to sustain multiple accounts
* No data at-rest should be de-anonymizing 

Assumptions:
* The main concern with phone company and corporate intermediaries is spying,
  but we depend on the legal system to prevent intermediaries from
  creating fraudulent interactions on behalf of the user.

Setup
-----
* In production, the Twilio portion should only white-list the Twilio server
* The admin section should also not be available on the public web, but should
  white-list only polling/administration stations


Things to worry about
---------------------
* Is there a way for a citizen to see if your vote was counted?
  (need the cool homomorphic protocol thing)
  What would need to be public?  phone hmacs?
* Is there a way to assure voters that the state isn't stuffing the ballot?
  (probably not!)

