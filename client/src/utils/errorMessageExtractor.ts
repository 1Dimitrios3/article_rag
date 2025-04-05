const extractErrorMessage = (error: any): string => {
    let message = error.message || "Something went wrong";
    try {
      const parsed = JSON.parse(message);
      if (Array.isArray(parsed) && parsed.length > 0 && parsed[0].message) {
        message = parsed[0].message;
      }
    } catch {
      // If JSON parsing fails, we'll simply use the original message.
    }
    return message;
  };

  export { extractErrorMessage };