# Chrome Region OCR Permission Review

The extension captures only an explicit `Alt` + drag selection and sends its
bounding box to an existing tenant-scoped accounting document.

## Permissions

| Permission | Reason |
| --- | --- |
| `activeTab` | Limit interaction to the page explicitly activated by the user. |
| `storage` | Store API URL, document context and bearer token locally. |
| `scripting` | Inject the selector only after the user clicks `Activate on this page`. |
| `http://localhost:8000/*` | Allow local development API calls only. Production packaging must replace this with the deployed API origin. |

The extension does not inject or capture automatically. The user must activate
the current page and then perform an explicit `Alt` + drag gesture. Dimensions
are validated client-side and again by the API.
