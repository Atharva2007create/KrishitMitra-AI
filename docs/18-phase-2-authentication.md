# Phase 2 authentication and authorization

Amazon Cognito authenticates users; FastAPI authorizes every protected request. The backend accepts bearer access or ID tokens only after RS256 signature verification against the pool JWKS, issuer validation, expiry validation, token-use validation, and client audience/client-id validation. JWKS keys are cached for a bounded interval.

The database links users by immutable Cognito `sub`. A new user is FARMER unless the verified token contains the configured `administrators` Cognito group. The persisted role is authoritative on later requests. Clients cannot select or elevate a role through request bodies. Farmer dependencies reject admins where a farmer-owned workflow is required, and admin dependencies return 403 for non-admins.

The development pool is on the Cognito Essentials tier and permits `PASSWORD` plus `SMS_OTP` as first factors. Its public app client permits `ALLOW_USER_AUTH`, `ALLOW_USER_SRP_AUTH`, and refresh-token authentication. Email and phone attributes are auto-verified, SMS delivery uses a dedicated Cognito-assumable IAM role with an external-ID condition, and MFA remains off because passwordless OTP cannot be combined with required MFA. Actual SMS messages can incur AWS End User Messaging charges and remain subject to the account SMS sandbox/spending limit. No test user or OTP was created during infrastructure configuration.

Farmer clients will initiate the `USER_AUTH` flow with the phone number and `PREFERRED_CHALLENGE=SMS_OTP`, then answer the returned `SMS_OTP` challenge. Admin clients continue to use email/password through SRP. Both flows produce Cognito JWTs consumed by the same backend verifier.

Admin bootstrap is deliberately password-free:

```bash
python -m scripts.bootstrap_admin --username EXISTING_COGNITO_USERNAME
```

The script adds an existing user to the trusted Cognito group and can update an already-created application user when `--cognito-sub` is supplied. It never creates a user or handles credentials. Authentication failures return 401; authenticated users without the required role receive 403. Logs and audit metadata must never include raw JWTs, OTP values, passwords, or secret contents.
