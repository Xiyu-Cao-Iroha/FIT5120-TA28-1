import { z } from "zod";

export const SensoryLevelSchema = z.enum(["low", "high", "unavailable"]);
export type SensoryLevel = z.infer<typeof SensoryLevelSchema>;

export const CongestedSegmentSchema = z.object({
  sequence: z.number(),
  geometry: z.string(),
  crowd_score: z.number().nullable(),
  sensory_level: SensoryLevelSchema,
});
export type CongestedSegment = z.infer<typeof CongestedSegmentSchema>;

export const RouteOptionSchema = z.object({
  id: z.string(),
  name: z.string(),
  duration_minutes: z.number(),
  distance_meters: z.number(),
  geometry: z.string(),
  sensory_level: SensoryLevelSchema,
  crowd_score: z.number().nullable(),
  data_coverage: z.number(),
  is_recommended: z.boolean(),
  explanation: z.string(),
  congested_segments: z.array(CongestedSegmentSchema),
  data_updated_at: z.string().nullable(),
  rule_version: z.string(),
});
export type RouteOption = z.infer<typeof RouteOptionSchema>;

export const RouteCompareResponseSchema = z.object({
  request_id: z.string(),
  snapshot_id: z.string(),
  rule_version: z.string(),
  routes: z.array(RouteOptionSchema),
});
export type RouteCompareResponse = z.infer<typeof RouteCompareResponseSchema>;

export const ErrorResponseSchema = z.object({
  error: z.object({
    code: z.string(),
    message: z.string(),
  }),
});
export type ApiErrorBody = z.infer<typeof ErrorResponseSchema>;

export const LatLonSchema = z.object({
  lat: z.number().min(-90).max(90),
  lon: z.number().min(-180).max(180),
});
export type LatLon = z.infer<typeof LatLonSchema>;

export const CrowdSensitivitySchema = z.enum(["low", "moderate", "high"]);
export type CrowdSensitivity = z.infer<typeof CrowdSensitivitySchema>;

export const RefugeSourceSchema = z.enum(["verified", "prototype"]);
export type RefugeSource = z.infer<typeof RefugeSourceSchema>;

export const RefugeSummarySchema = z.object({
  id: z.string(),
  name: z.string(),
  category: z.string(),
  address: z.string(),
  lat: z.number(),
  lon: z.number(),
  distance_meters: z.number(),
  short_description: z.string(),
  data_source: RefugeSourceSchema,
});
export type RefugeSummary = z.infer<typeof RefugeSummarySchema>;

export const RefugeListResponseSchema = z.object({
  route_id: z.string(),
  refuges: z.array(RefugeSummarySchema),
});
export type RefugeListResponse = z.infer<typeof RefugeListResponseSchema>;

export const RefugeDetailSchema = RefugeSummarySchema.extend({
  facility_info: z.string(),
  source_note: z.string(),
});
export type RefugeDetail = z.infer<typeof RefugeDetailSchema>;

export const PlaceSuggestionSchema = z.object({
  place_id: z.string(),
  description: z.string(),
});
export type PlaceSuggestion = z.infer<typeof PlaceSuggestionSchema>;

export const PlaceSearchResponseSchema = z.object({
  suggestions: z.array(PlaceSuggestionSchema),
});
export type PlaceSearchResponse = z.infer<typeof PlaceSearchResponseSchema>;

export const ResolvedPlaceSchema = z.object({
  place_id: z.string(),
  description: z.string(),
  lat: z.number(),
  lon: z.number(),
});
export type ResolvedPlace = z.infer<typeof ResolvedPlaceSchema>;
