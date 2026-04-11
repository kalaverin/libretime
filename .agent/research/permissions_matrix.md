# LibreTime Permissions Matrix

**Visual reference for all permissions and their application**

---

## Legend

| Symbol | Meaning |
|--------|---------|
| ✅ | Allowed |
| ❌ | Denied |
| 🔴 | Vulnerable (no queryset filter) |
| 🟢 | Fixed |
| 👤 | Own objects only |
| 🌐 | All objects |

---

## Role Permissions Overview

### GUEST ("G")
```
┌─────────────────────────────────────────────────────────────┐
│  VIEW PERMISSIONS ONLY                                      │
├─────────────────────────────────────────────────────────────┤
│  view_schedule     view_show           view_showdays        │
│  view_showhost     view_showinstance   view_showrebroadcast │
│  view_file         view_podcast        view_podcastepisode  │
│  view_playlist     view_playlistcontent                     │
│  view_smartblock   view_smartblockcontent                   │
│  view_smartblockcriteria  view_webstream  view_apiroot      │
└─────────────────────────────────────────────────────────────┘
```

### HOST ("H")
```
┌─────────────────────────────────────────────────────────────┐
│  GUEST + CREATE + OWN MODIFICATIONS                         │
├─────────────────────────────────────────────────────────────┤
│  ADD:                                                      │
│  add_file, add_podcast, add_podcastepisode                  │
│  add_playlist, add_playlistcontent                          │
│  add_smartblock, add_smartblockcontent, add_smartblockcriteria│
│  add_webstream                                              │
├─────────────────────────────────────────────────────────────┤
│  OWN_*: (Custom Model Permissions)                         │
│  change_own_*  delete_own_*                                │
│  ↳ file, playlist, playlistcontent                         │
│  ↳ smartblock, smartblockcontent, smartblockcriteria       │
│  ↳ webstream, schedule, podcast, podcastepisode            │
└─────────────────────────────────────────────────────────────┘
```

### MANAGER ("P")
```
┌─────────────────────────────────────────────────────────────┐
│  FULL CRUD ON ALL OBJECTS                                   │
├─────────────────────────────────────────────────────────────┤
│  Show Management: add/change/delete_show*                   │
│  File: add/change/delete_file                               │
│  Podcast: add/change/delete_podcast, podcastepisode         │
│  Playlist: add/change/delete_playlist, playlistcontent      │
│  SmartBlock: add/change/delete_smartblock*                  │
│  WebStream: add/change/delete_webstream                     │
│  Schedule: change/delete_schedule                           │
└─────────────────────────────────────────────────────────────┘
```

---

## ViewSet Permission Matrix

### Schedule Module

| ViewSet | Model | GUEST | HOST | MANAGER | Queryset Filter | Status |
|---------|-------|-------|------|---------|-----------------|--------|
| **ShowViewSet** | show | view | view | CRUD | Returns all | ⚠️ Design issue? |
| **ShowDaysViewSet** | showdays | view | view | CRUD | None | 🔴 Missing filter |
| **ShowHostViewSet** | showhost | view | view | CRUD | None | 🔴 Missing filter |
| **ShowInstanceViewSet** | showinstance | view | view | CRUD | None | 🔴 Missing filter |
| **ShowRebroadcastViewSet** | showrebroadcast | view | view | CRUD | None | 🔴 Missing filter |
| **PlaylistViewSet** | playlist | view | own CRUD | CRUD | None | 🔴 **BOLA** |
| **PlaylistContentViewSet** | playlistcontent | view | own CRUD | CRUD | playlist filter only | 🔴 **BOLA** |
| **SmartBlockViewSet** | smartblock | view | own CRUD | CRUD | kind filter only | 🔴 **BOLA** |
| **SmartBlockContentViewSet** | smartblockcontent | view | own CRUD | CRUD | block filter only | 🔴 **BOLA** |
| **SmartBlockCriteriaViewSet** | smartblockcriteria | view | own CRUD | CRUD | block filter only | 🔴 **BOLA** |
| **ScheduleViewSet** | schedule | view | own modify | modify | None | 🔴 Missing filter |
| **WebstreamViewSet** | webstream | view | own CRUD | CRUD | ✅ Owner filter | 🟢 Fixed |
| **WebstreamMetadataViewSet** | webstreammetadata | view | own CRUD | CRUD | None | 🔴 Missing filter |

### Storage Module

| ViewSet | Model | GUEST | HOST | MANAGER | Queryset Filter | Status |
|---------|-------|-------|------|---------|-----------------|--------|
| **FileViewSet** | file | view | own CRUD | CRUD | None | 🔴 **BOLA** |
| **LibraryViewSet** | library | view | view? | CRUD | None | 🔴 Missing filter |

### Podcasts Module

| ViewSet | Model | GUEST | HOST | MANAGER | Queryset Filter | Status |
|---------|-------|-------|------|---------|-----------------|--------|
| **PodcastViewSet** | podcast | view | own CRUD? | CRUD | None | 🔴 Missing filter |
| **PodcastEpisodeViewSet** | podcastepisode | view | own CRUD? | CRUD | None | 🔴 Missing filter |
| **StationPodcastViewSet** | station | view | ? | CRUD | None | 🔴 Missing filter |
| **ImportedPodcastViewSet** | importedpodcast | view | ? | CRUD | None | 🔴 Missing filter |

### Core Module

| ViewSet | Model | GUEST | HOST | MANAGER | ADMIN | Special |
|---------|-------|-------|------|---------|-------|---------|
| **UserViewSet** | user | ❌ | own | own | CRUD | IsAdminOrOwnUser |
| **PreferenceViewSet** | preference | ? | ? | ? | ? | Default |
| **ServiceRegisterViewSet** | serviceregister | ? | ? | ? | ? | Default |
| **UserTokenViewSet** | usertoken | ❌ | own | own | CRUD | Default |
| **LoginAttemptViewSet** | loginattempt | ❌ | ? | ? | CRUD | Default |
| **StreamSettingViewSet** | streamsetting | ❌ | ❌ | ❌ | CRUD | IsSystemTokenOrUser |

### History Module

| ViewSet | Model | GUEST | HOST | MANAGER | Status |
|---------|-------|-------|------|---------|--------|
| **PlayoutHistoryViewSet** | playouthistory | view | view | CRUD | 🔴 Missing filter |
| **PlayoutHistoryMetadataViewSet** | playouthistorymetadata | view | view | CRUD | 🔴 Missing filter |
| **PlayoutHistoryTemplateViewSet** | playouthistorytemplate | view | view | CRUD | 🔴 Missing filter |
| **PlayoutHistoryTemplateFieldViewSet** | playouthistorytemplatefield | view | view | CRUD | 🔴 Missing filter |
| **MountNameViewSet** | mountname | view | view | CRUD | 🔴 Missing filter |
| **TimestampViewSet** | timestamp | view | view | CRUD | 🔴 Missing filter |
| **ListenerCountViewSet** | listenercount | view | view | CRUD | 🔴 Missing filter |
| **LiveLogViewSet** | livelog | view | view | CRUD | 🔴 Missing filter |

---

## Permission Class Usage

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         PERMISSION CLASS MAP                             │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  IsSystemTokenOrUser (Default)                                          │
│  ├── Schedule Views (10 ViewSets)                                       │
│  ├── Storage Views (2 ViewSets)                                         │
│  ├── Podcast Views (4 ViewSets)                                         │
│  ├── Core Views (6 ViewSets except User)                                │
│  ├── History Views (8 ViewSets)                                         │
│  └── StreamPreferencesViewSet (explicit)                                │
│                                                                          │
│  IsAdminOrOwnUser                                                       │
│  └── UserViewSet only                                                   │
│                                                                          │
│  AllowAny                                                               │
│  ├── InfoViewSet                                                        │
│  └── VersionViewSet                                                     │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Custom Model Permissions

| Model | Custom Permission | Human Name | Applied To |
|-------|------------------|------------|------------|
| Schedule | change_own_schedule | Change the content on their shows | HOST |
| Schedule | delete_own_schedule | Delete the content on their shows | HOST |
| File | change_own_file | Change the files where they are the owner | HOST |
| File | delete_own_file | Delete the files where they are the owner | HOST |
| Webstream | change_own_webstream | Change the webstreams where they are the owner | HOST |
| Webstream | delete_own_webstream | Delete the webstreams where they are the owner | HOST |
| SmartBlock | change_own_smartblock | Change the smartblocks where they are the owner | HOST |
| SmartBlockContent | change_own_smartblockcontent | Change the content of smartblocks where they are the owner | HOST |
| SmartBlockContent | delete_own_smartblockcontent | Delete the content of smartblocks where they are the owner | HOST |
| SmartBlockCriteria | change_own_smartblockcriteria | Change the criteria of smartblocks where they are the owner | HOST |
| SmartBlockCriteria | delete_own_smartblockcriteria | Delete the criteria of smartblocks where they are the owner | HOST |

---

## HTTP Method to Permission Mapping

```
┌─────────────────────────────────────────────────────────────┐
│              REQUEST_PERMISSION_TYPE_MAP                     │
├─────────────┬───────────────────────────────────────────────┤
│ HTTP Method │ Permission Prefix                               │
├─────────────┼───────────────────────────────────────────────┤
│ GET         │ view_                                          │
│ HEAD        │ view_                                          │
│ OPTIONS     │ view_                                          │
│ POST        │ change_  (NOTE: should be add_)                │
│ PUT         │ change_                                        │
│ PATCH       │ change_                                        │
│ DELETE      │ delete_                                        │
└─────────────┴───────────────────────────────────────────────┘

Final Permission: {action}_{own_prefix}{model_name}
Example: change_own_playlist
```

---

## BOLA Vulnerability Summary

| ViewSet | Vulnerability | Attack Vector | Impact |
|---------|--------------|---------------|--------|
| PlaylistViewSet | No owner filter | GET /playlists/{id} | Read any playlist |
| PlaylistViewSet | No owner filter | PATCH /playlists/{id} | Modify any playlist |
| PlaylistViewSet | No owner filter | DELETE /playlists/{id} | Delete any playlist |
| SmartBlockViewSet | No owner filter | GET /smart-blocks/{id} | Read any block |
| SmartBlockViewSet | No owner filter | PATCH /smart-blocks/{id} | Modify any block |
| SmartBlockViewSet | No owner filter | DELETE /smart-blocks/{id} | Delete any block |
| FileViewSet | No owner filter | GET /files/{id} | Read any file metadata |
| FileViewSet | No owner filter | GET /files/{id}/download | Download any file |
| FileViewSet | No owner filter | DELETE /files/{id} | Delete any file |

---

## Fix Implementation Template

```python
# For models with 'owner' field
class SecureViewSet(ModelViewSet):
    
    def get_queryset(self):
        # Service auth: full access
        if check_authorization_header(self.request):
            return self.queryset
        
        user = self.request.user
        
        # Anonymous: no access
        if not user.is_authenticated:
            return self.queryset.none()
        
        # Admin: full access
        if user.is_superuser:
            return self.queryset
        
        # Regular user: own objects only
        return self.queryset.filter(owner=user)
    
    def perform_create(self, serializer):
        user = self.request.user
        if user.is_authenticated and not user.is_anonymous:
            from api.core.models import User
            if isinstance(user, User):
                serializer.save(owner=user)
                return
        serializer.save()
```

---

## Files to Fix

1. `app/api/api/schedule/views/playlist.py` - PlaylistViewSet, PlaylistContentViewSet
2. `app/api/api/schedule/views/smart_block.py` - SmartBlockViewSet, SmartBlockContentViewSet, SmartBlockCriteriaViewSet
3. `app/api/api/storage/views/file.py` - FileViewSet
4. `app/api/api/schedule/views/show.py` - ShowDaysViewSet, ShowHostViewSet, ShowInstanceViewSet, ShowRebroadcastViewSet (if needed)

---

*Generated: 2026-04-10T23:35:00Z*
