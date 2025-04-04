import { baseUrl } from "~/config";

export async function fetchIntegratorData() {
    const response = await fetch(`${baseUrl}/api/check-integrators`);
    if (!response.ok) {
      throw new Error('Network response was not ok');
    }
    return response.json();
  }