from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from datetime import datetime, timezone, timedelta
import json
import time

# Update scopes to include all fitness data
SCOPES = [
    'https://www.googleapis.com/auth/fitness.activity.read',
    'https://www.googleapis.com/auth/fitness.heart_rate.read',
    'https://www.googleapis.com/auth/fitness.body.read',
    'https://www.googleapis.com/auth/fitness.location.read'
]


# Load credentials and authenticate
def authenticate():
    try:
        # First, let's print the contents of the client secrets file to see the configured redirect URIs
        with open('client_secret_247707654993-570ulm9dcot7tn929ngnci7dl2f6tdp9.apps.googleusercontent.com-2.json',
                  'r') as f:
            client_secrets = json.load(f)
            print("\nConfigured redirect URIs:", client_secrets.get('web', {}).get('redirect_uris', []))

        flow = InstalledAppFlow.from_client_secrets_file(
            'client_secret_247707654993-570ulm9dcot7tn929ngnci7dl2f6tdp9.apps.googleusercontent.com-2.json',
            SCOPES)

        # Use the correct port from the client secrets
        creds = flow.run_local_server(
            port=49253,  # Match the configured redirect URI
            success_message='The authentication flow has completed. You may close this window.',
            open_browser=True
        )
        return creds
    except Exception as e:
        print(f"Authentication error: {str(e)}")
        raise


# Fetch fitness data
def get_fitness_data():
    try:
        # Only authenticate once at startup
        if not hasattr(get_fitness_data, 'creds'):
            get_fitness_data.creds = authenticate()
            get_fitness_data.last_hr = None
            get_fitness_data.last_time = None
            print('\033[2J\033[H', end='')  # Clear screen after auth

        service = build('fitness', 'v1', credentials=get_fitness_data.creds)

        # Set time range for last 10 seconds
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(seconds=10)

        body = {
            "aggregateBy": [{
                "dataTypeName": "com.google.heart_rate.bpm",
                "dataSourceId": "derived:com.google.heart_rate.bpm:com.google.android.gms:merge_heart_rate_bpm"
            }],
            "bucketByTime": {"durationMillis": 10000},
            "startTimeMillis": int(start_time.timestamp() * 1000),
            "endTimeMillis": int(end_time.timestamp() * 1000)
        }

        response = service.users().dataset().aggregate(
            userId="me",
            body=body
        ).execute()

        latest_hr = None
        latest_time = None

        # Find the latest heart rate reading
        for bucket in reversed(response.get("bucket", [])):
            bucket_time = datetime.fromtimestamp(int(bucket['startTimeMillis']) / 1000, timezone.utc)
            local_time = bucket_time.astimezone()

            for dataset in bucket.get("dataset", []):
                points = dataset.get("point", [])
                if points:
                    for point in points:
                        values = point.get("value", [])
                        if values:
                            hr_value = values[0].get('fpVal')
                            if hr_value:
                                latest_hr = hr_value
                                latest_time = local_time
                                break
                if latest_hr:
                    break
            if latest_hr:
                break

        # Only update display if we have new data
        if latest_hr and (latest_hr != get_fitness_data.last_hr or
                          latest_time != get_fitness_data.last_time):
            print('\033[2J\033[H', end='')  # Clear screen
            print("Real-time Heart Rate Monitor")
            print("--------------------------------------------------------------")
            print(f"Heart Rate: {latest_hr:.0f} BPM at {latest_time.strftime('%I:%M:%S %p')}")
            print("\nMonitoring for new readings...")  # Add status message

            # Store latest values
            get_fitness_data.last_hr = latest_hr
            get_fitness_data.last_time = latest_time
            return True  # Indicate we got new data

        return False  # No new data

    except Exception as e:
        print(f"Error: {str(e)}")
        return False


def monitor_latest_data():
    print('\033[2J\033[H', end='')  # Clear screen once at start
    print("Real-time Heart Rate Monitor")
    print("--------------------------------------------------------------")
    print("Waiting for heart rate data...")

    consecutive_failures = 0
    while True:
        if get_fitness_data():
            consecutive_failures = 0
        else:
            consecutive_failures += 1
            if consecutive_failures > 30:  # After 30 seconds of no data
                print('\033[2J\033[H', end='')
                print("Real-time Heart Rate Monitor")
                print("--------------------------------------------------------------")
                print("Waiting for new heart rate data...")
                consecutive_failures = 0

        time.sleep(1)  # Check every second for new data


# Run the function
if __name__ == "__main__":
    monitor_latest_data()