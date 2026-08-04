import { useQuery } from "@tanstack/react-query";

import { getRefugeDetail, getRefuges, getRouteDetail, postRouteCompare } from "./client";
import {
  type CrowdSensitivity,
  type LatLon,
  type RefugeDetail,
  type RefugeListResponse,
  type RouteCompareResponse,
  type RouteOption,
  RefugeDetailSchema,
  RefugeListResponseSchema,
  RouteCompareResponseSchema,
  RouteOptionSchema,
} from "./schemas";

export function useRouteComparison(
  origin: LatLon | null,
  destination: LatLon | null,
  crowdSensitivity: CrowdSensitivity | null
) {
  return useQuery<RouteCompareResponse>({
    queryKey: ["routes", "compare", origin, destination, crowdSensitivity],
    queryFn: async () => {
      const raw = await postRouteCompare({ origin, destination, crowd_sensitivity: crowdSensitivity });
      return RouteCompareResponseSchema.parse(raw);
    },
    enabled: Boolean(
      origin &&
        destination &&
        Number.isFinite(origin.lat) &&
        Number.isFinite(origin.lon) &&
        Number.isFinite(destination.lat) &&
        Number.isFinite(destination.lon)
    ),
    retry: false,
  });
}

export function useRouteDetail(routeId: string | undefined) {
  return useQuery<RouteOption>({
    queryKey: ["routes", "detail", routeId],
    queryFn: async () => {
      const raw = await getRouteDetail(routeId as string);
      return RouteOptionSchema.parse(raw);
    },
    enabled: Boolean(routeId),
    retry: false,
  });
}

export function useRefuges(routeId: string | undefined) {
  return useQuery<RefugeListResponse>({
    queryKey: ["refuges", "list", routeId],
    queryFn: async () => {
      const raw = await getRefuges(routeId as string);
      return RefugeListResponseSchema.parse(raw);
    },
    enabled: Boolean(routeId),
    retry: false,
  });
}

export function useRefugeDetail(placeId: string | undefined, routeId: string | undefined) {
  return useQuery<RefugeDetail>({
    queryKey: ["refuges", "detail", placeId, routeId],
    queryFn: async () => {
      const raw = await getRefugeDetail(placeId as string, routeId as string);
      return RefugeDetailSchema.parse(raw);
    },
    enabled: Boolean(placeId && routeId),
    retry: false,
  });
}
