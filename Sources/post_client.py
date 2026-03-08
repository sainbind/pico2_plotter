import sys
import requests


def read_file_as_string(file_path):
    """
    Read the contents of a file and return it as a string.

    :param file_path: The path to the file to read.
    :return: The contents of the file as a string, or None if an error occurs.
    """
    try:
        with open(file_path, 'r') as f:
            return f.read()
    except Exception as e:
        print(f"Failed to read file {file_path}: {e}")
        return None


def send_post_request(url, file_path: str, headers=None):
    """
    Send an HTTP POST request.

    :param url: The URL to send the POST request to.
    :param file_path: A file of gcode commands to send as the request body
    :return: Response text on success, None on failure.
    """
    data = read_file_as_string(file_path)
    headers = {"Content-Type": "plain/text"}

    try:
        print(f"Posting {file_path} to {url}\n")
        #print(f"Request\n: {data}")
        response = requests.post(url, data=data, headers=headers)
        result = response.text
        status = response.status_code
        response.close()
        print(f"Post result: {status}")
        return result
    except Exception as e:
        print(f"Post request failed: {e}")
        return None



if __name__ == "__main__":
    # Example usage
    url = "http://192.168.4.111:5000/run"
    file_path = sys.argv[1] if len(sys.argv) > 1 else "./relative.gcode"
    result = send_post_request(url, file_path)
    print("\nResponse:\n", result)

