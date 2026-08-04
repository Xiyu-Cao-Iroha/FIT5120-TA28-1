import { ApiRequestError } from "../api/client";

interface ErrorPresentation {
  title: string;
  message: string;
  action: "retry" | "edit" | null;
}

// Maps the backend error contract (requirements section 9.4 / 7) to the
// copy and recovery action shown on RouteResultsScreen.
export function describeApiError(error: unknown): ErrorPresentation {
  if (error instanceof ApiRequestError) {
    switch (error.code) {
      case "OUTSIDE_SERVICE_AREA":
        return {
          title: "Destination is outside the service area",
          message:
            "CalmPath currently only compares routes within the Melbourne CBD. Please choose a different destination.",
          action: "edit",
        };
      case "INVALID_LOCATION":
        return {
          title: "Invalid origin or destination",
          message: error.message,
          action: "edit",
        };
      case "NO_ROUTE_FOUND":
        return {
          title: "No walking route found",
          message: "We couldn't find a walking route between these two points.",
          action: "edit",
        };
      case "RATE_LIMITED":
        return {
          title: "Too many requests",
          message: "Please wait a moment before comparing routes again.",
          action: "retry",
        };
      case "DATA_SOURCE_UNAVAILABLE":
        return {
          title: "Pedestrian data temporarily unavailable",
          message: "The open-data source is currently unavailable. You can retry, or try again later.",
          action: "retry",
        };
      default:
        return {
          title: "Something went wrong",
          message: "An unexpected error occurred. Please try again.",
          action: "retry",
        };
    }
  }
  return {
    title: "Connection problem",
    message: "Couldn't reach the CalmPath server. Check your connection and try again.",
    action: "retry",
  };
}
