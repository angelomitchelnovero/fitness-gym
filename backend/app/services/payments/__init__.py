"""Payment provider abstraction.

Real providers (GCash, Maya, Stripe, etc.) plug in here by implementing
`PaymentProvider`. Membership activation lives in `payment_service`, not in
the providers — providers only create/verify/cancel charges.
"""