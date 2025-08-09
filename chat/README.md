# Chat GraphQL API Usage

This document explains how to use the chat GraphQL queries and mutation that power conversations and messages.

## Overview

You can:

- List a user's conversations
- List messages in a conversation
- Send a new message (creates a conversation if none provided) and receive an AI reply

All operations require an authenticated user (JWT) except they return empty lists when unauthenticated.

## Schema Elements

### Types (from `chat/schema/types.py`)

Note: Current `ConversationType` and `MessageType` expect model fields `(id, title, created_at)` and `(id, conversation, role, content, model, created_at)`. Ensure your `Message` model has `role` and `model` fields; if not, align the type or model accordingly.

```graphql
ConversationType {
  id: ID!
  title: String
  created_at: DateTime
}

MessageType {
  id: ID!
  conversation: ConversationType!
  role: String
  content: String
  model: String
  created_at: DateTime
}
```

### Queries

1. conversations: `[ConversationType]`
   Returns the authenticated user's conversations ordered by newest.

2. messages(conversation_id: ID!): `[MessageType]`
   Returns messages for a conversation owned by the user. Empty if conversation doesn't belong to the user or not found.

### Mutation

`sendMessage(conversationId, content, model)` -> `{ ok, conversation, userMessage, aiMessage }`

- If `conversationId` omitted, a new conversation is created (title derived from first message).
- AI reply is generated and saved.

## Examples

### Authenticate (Obtain Token)

```graphql
mutation Login($username: String!, $password: String!) {
  tokenAuth(username: $username, password: $password) {
    token
    payload { username exp }
  }
}
```

### List Conversations

```graphql
query Conversations {
  conversations {
    id
    title
    created_at
  }
}
```

### List Messages

```graphql
query Messages($id: ID!) {
  messages(conversationId: $id) {
    id
    role
    content
    created_at
  }
}
```
(Adjust field names if using `conversation_id` vs `conversationId` depending on your GraphQL naming—Graphene auto-camelCases.)

### Send Message

```graphql
mutation Send($content: String!, $cid: ID) {
  sendMessage(content: $content, conversationId: $cid) {
    ok
    conversation { id title }
    userMessage { id role content }
    aiMessage { id role content }
  }
}
```

Variables:

```json
{ "content": "Explain CQRS briefly", "cid": null }
```

### Refresh Token

```graphql
mutation Refresh($token: String!) {
  refreshToken(token: $token) {
    token
    payload { exp }
  }
}
```

## HTTP Headers

```text
Authorization: JWT <token>
```

## WebSocket Usage (ChatConsumer)

1. Connect with `?token=<JWT>` OR send `{ "token": "<JWT>" }` as the first message.
2. Then send `{ "message": "Hello" }`.
3. Receive AI response as `{ "response": "..." }`.
4. If you receive `TOKEN_EXPIRED`, refresh and reconnect.

## Alignment Note

If your `Message` model currently uses `sender` (FK) instead of `role`/`model`, update the GraphQL `MessageType` or add those fields. The mutation/service code uses `role`/`model` fields (`Message.objects.create(... role="user" ...)`). Ensure those exist in your `Message` model or adjust to use `sender` with `sender.role` semantics.

## Troubleshooting

- Empty `conversations` or `messages`: likely unauthenticated or wrong conversation owner.
- `TOKEN_EXPIRED`: refresh and retry.
- Schema mismatch (e.g., `Cannot query field "role" on type "MessageType"`): sync `MessageType` with your actual model fields.

## Next Steps

- Add pagination for messages.
- Add delete / rename conversation mutations.
- Add message editing & reaction mutations.

