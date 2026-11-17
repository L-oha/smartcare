# SmartCare manual MVP checklist

Use a fresh demo account and record Pass or Fail after each browser check.

| Scenario | Steps | Expected result | Result |
|---|---|---|---|
| Open the app | Start Compose and open http://127.0.0.1:8000 | SmartCare homepage appears | Pending |
| Register | Click Get started and submit a new email, name, and password | Patient dashboard appears | Pending |
| Sign in | Sign out, then sign in with the same account | Patient dashboard appears again | Pending |
| Book | Select a provider, open availability, and book a future slot | The appointment appears as confirmed | Pass |
| Cancel | Cancel the appointment and reopen the same provider's availability | Appointment shows cancelled and its slot is available again | Pass |

## Manual test results — November 14, 2026

I tested SmartCare in Safari on my Mac while the app was running locally in Docker.

- Provider availability — Pass. Dr. Maya Johnson’s available times loaded.
- Booking — Pass. I booked November 16, 2026 at 9:00 AM, and My Appointments showed it as confirmed.
- Cancellation — Pass. My Appointments changed the same booking to cancelled.
- Slot reopening — Pass. I returned to Dr. Maya Johnson’s availability page and verified that the same 9:00 AM slot had a Book button again. 
