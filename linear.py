import requests
import json
import sqlite3

LINEAR_API_TOKEN = "lin_api_8YHttL95Z268z38jvluYRaRHl6aW7DXIealAwlpz"
TEAM_ID = "907e99f2-9d02-4126-ad7b-794611e94a27"  # Use the correct Linear team ID
COMPLETED_STATE_ID = "9941892d-25da-4884-a1a5-5780c6b04911"  # Replace with your "Done" state ID
# Function to create a Linear task and assign it to a specific person
# Define the state ID for "Completed" in Linear
def update_linear_task_assignee(task_id, new_assignee_id):
    url = "https://api.linear.app/graphql"

    """
    Updates the assignee of a Linear task using the task ID and new assignee's ID.
    
    :param task_id: The ID of the Linear task (issue) to update
    :param new_assignee_id: The ID of the new assignee (Linear user)
    :return: True if the update was successful, False otherwise
    """
    # GraphQL mutation to update the issue (task) assignee
    query = """
    mutation UpdateIssue($issueId: String!, $assigneeId: String!) {
      issueUpdate(id: $issueId, input: { assigneeId: $assigneeId }) {
        success
        issue {
          id
          assignee {
            id
            name
          }
        }
      }
    }
    """
    
    # Define the variables for the mutation
    variables = {
        "issueId": task_id,
        "assigneeId": new_assignee_id
    }

    # Set the headers with the API key for authentication
    headers = {
        "Authorization": f"{LINEAR_API_TOKEN}",
        "Content-Type": "application/json"
    }

    # Send the request to the Linear API
    response = requests.post(url, json={"query": query, "variables": variables}, headers=headers)

    if response.status_code == 200:
        data = response.json()
        if data.get("data", {}).get("issueUpdate", {}).get("success", False):
            print(f"Task {task_id} successfully reassigned to user {new_assignee_id}.")
            return True
        else:
            print(f"Failed to reassign task {task_id}.")
    else:
        print(f"Failed to reach Linear API: {response.status_code}, {response.text}")
    
    return False
def create_linear_task(person_name, bed_number, assignee_id, start_time=None, end_time=None, due_date=None):
    url = "https://api.linear.app/graphql"
    headers = {
        "Authorization": f"{LINEAR_API_TOKEN}",
        "Content-Type": "application/json"
    }

    # Define the GraphQL query
    query = """
    mutation($teamId: String!, $title: String!, $description: String!, $assigneeId: String!, $dueDate: TimelessDate) {
        issueCreate(input: {teamId: $teamId, title: $title, description: $description, assigneeId: $assigneeId, dueDate: $dueDate}) {
            success
            issue {
                id
                title
                assignee {
                    id
                    name
                }
            }
        }
    }
    """

    # Define title and description with timeframes if provided
    title = f"Task assigned to {person_name} (Bed {bed_number})"
    description = f"Bed {bed_number} has been assigned to {person_name}."
    
    if start_time and end_time:
        description += f" Start Time: {start_time}, End Time: {end_time}."
    else:
        description += " Please review the task."

    # Ensure assignee_id is a string
    if not isinstance(assignee_id, str):
        assignee_id = str(assignee_id)

    payload = {
        "query": query,
        "variables": {
            "teamId": TEAM_ID,
            "title": title,
            "description": description,
            "assigneeId": assignee_id,
            "dueDate": due_date  # Make sure dueDate is in the format "YYYY-MM-DD"
        }
    }

    # Print payload for debugging
    print(f"Payload: {json.dumps(payload, indent=2)}")

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))

        # Print full response for debugging
        print(f"Response Status Code: {response.status_code}")
        print(f"Response Content: {response.text}")

        if response.status_code == 200:
            data = response.json()
            issue = data.get("data", {}).get("issueCreate", {}).get("issue", {})
            if issue:
                task_id = issue.get("id")
                assignee = issue.get("assignee", {}).get("name")
                print(f"Task created: {issue['title']} (ID: {task_id}), Assigned to: {assignee}")
                return task_id
            else:
                print(f"Error: No issue returned in response: {data}")
        else:
            print(f"Error creating task: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"An exception occurred: {str(e)}")

    return None


# Fetch Linear team members and populate the 'people' table
def fetch_and_populate_linear_team():
    url = "https://api.linear.app/graphql"
    headers = {
        "Authorization": f"{LINEAR_API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    query = """
    {
        users {
            nodes {
                id
                name
                email
            }
        }
    }
    """
    
    response = requests.post(url, headers=headers, data=json.dumps({"query": query}))
    
    if response.status_code == 200:
        data = response.json()
        members = data.get("data", {}).get("users", {}).get("nodes", [])

        # Insert fetched members into the SQLite `people` table
        conn = sqlite3.connect('production.db')
        c = conn.cursor()

        # Clear the current people table
        c.execute("DELETE FROM people")
        
        # Insert new people with their Linear user IDs
        for member in members:
            c.execute('INSERT OR IGNORE INTO people (name, linear_user_id) VALUES (?, ?)', (member['name'], member['id']))
        
        conn.commit()
        conn.close()

        print("Successfully updated team members from Linear into the database.")
    else:
        print(f"Error fetching team members from Linear: {response.status_code} - {response.text}")

# Function to get all team members from Linear
def get_linear_team_members():
    url = "https://api.linear.app/graphql"
    headers = {
        "Authorization": f"{LINEAR_API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    query = """
    {
        users {
            nodes {
                id
                name
                email
            }
        }
    }
    """
    
    response = requests.post(url, headers=headers, data=json.dumps({"query": query}))
    
    if response.status_code == 200:
        data = response.json()
        members = data.get("data", {}).get("users", {}).get("nodes", [])
        for member in members:
            print(f"Member: {member['name']} (ID: {member['id']}) - Email: {member['email']}")
        return members
    else:
        print(f"Error fetching team members: {response.status_code} - {response.text}")
        return []



# Function to mark a task as complete
def mark_task_complete(task_id, completed_state_id):
    url = "https://api.linear.app/graphql"
    headers = {
        "Authorization": f"{LINEAR_API_TOKEN}",
        "Content-Type": "application/json"
    }

    query = """
    mutation($id: String!, $stateId: String!) {
        issueUpdate(id: $id, input: {stateId: $stateId}) {
            success
            issue {
                id
                state {
                    name
                }
            }
        }
    }
    """

    payload = {
        "query": query,
        "variables": {
            "id": task_id,
            "stateId": completed_state_id  # "Done" state ID
        }
    }

    print(f"Marking task {task_id} as complete...")  # First print statement

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        print(f"Response status code: {response.status_code}")  # Print response status code

        if response.status_code == 200:
            data = response.json()
            print(f"Response data: {data}")  # Print the entire response data for debugging

            if data.get("data", {}).get("issueUpdate", {}).get("success"):
                updated_issue = data["data"]["issueUpdate"]["issue"]
                print(f"Task marked as complete: {updated_issue['id']} - State: {updated_issue['state']['name']}")
            else:
                print(f"Failed to mark task as complete: {data}")
        else:
            print(f"Error: {response.status_code} - {response.text}")  # Print response status and text if it fails
    except Exception as e:
        print(f"An exception occurred: {str(e)}")  # Catch any exceptions and print them
