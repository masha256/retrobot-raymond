# Fixing Drive ownership transfer (`role=owner`) 403s

A thin Drive API wrapper that only forwards `sendNotificationEmail` (e.g.
via a `--notify` flag) to `permissions().create()` will fail in two stages
when asked to set `role=owner`:

1. First attempt:
   ```
   HttpError 403: The transferOwnership parameter must be enabled when the
   permission role is 'owner'.
   ```
2. After adding `transferOwnership=True`, a second failure appears:
   ```
   HttpError 403: The sendNotificationEmail parameter is only applicable for
   permissions of type 'user' or 'group', and must not be disabled for
   ownership transfers.
   ```
   Google forces notification email ON for ownership transfers specifically,
   overriding whatever the caller requested for a normal share.

## The fix

Wherever the wrapper builds the `permissions().create()` call:

```python
    service = build_service("drive", "v3")
    result = service.permissions().create(
        fileId=file_id,
        body=permission,          # {"type": ..., "role": ..., "emailAddress": ...}
        sendNotificationEmail=notify_flag,
        fields="id",
    ).execute()
```

change to:

```python
    service = build_service("drive", "v3")
    is_ownership_transfer = (permission["role"] == "owner")
    result = service.permissions().create(
        fileId=file_id,
        body=permission,
        sendNotificationEmail=(True if is_ownership_transfer else notify_flag),
        transferOwnership=is_ownership_transfer,
        fields="id",
    ).execute()
```

If the wrapper has an alternate code path that shells out to a separate
CLI binary instead of calling the API directly, the same two parameters
(`transferOwnership`, `sendNotificationEmail`) need to be added to that
path's request body/params as well — both paths must handle `role=owner`
identically.

## Verifying the fix

```bash
# however the wrapper exposes this:
<cli> drive share FILE_ID --email newowner@example.com --role owner
# expect: {"status": "shared", ..., "role": "owner"}

<cli> drive get FILE_ID
# "owners" field should now list newowner@example.com
```

## Scope note

Ownership transfer between two accounts **on the same Google Workspace
domain** works with no extra steps once the fix above is in place.
Transferring ownership to an **external consumer Gmail account** is
blocked by Google entirely, regardless of any client-side fix — that's a
platform limitation, not a bug to patch around.
