import { useQuery } from "@tanstack/react-query";
import { parseRead, parseWrite } from "./api";
import { useWallet } from "./store";
import type { Rsure } from "../wasm";
import type { State, WriteEnvelope } from "./types";

/** Contract arms usually reply `(true, value)`; peel that wrapper for state views. */
export function unwrap<T = State>(data: unknown): T {
  // `(true, value)` replies decode as `[true, value]`; `(true, Nil)` decodes as `[true]`,
  // so the value slot is absent rather than a null placeholder.
  if (Array.isArray(data) && data[0] === true && data.length <= 2) {
    return data[1] as T;
  }
  return data as T;
}

export function asState(data: unknown): State {
  const value = unwrap(data);
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as State)
    : {};
}

export function asList(data: unknown): State[] {
  const value = unwrap(data);
  return Array.isArray(value) ? (value.filter((item) => item && typeof item === "object") as State[]) : [];
}

export function asMap(data: unknown): Record<string, State> {
  const value = unwrap(data);
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, State>)
    : {};
}

export function useRead<T = State>(
  component: string,
  arm: string,
  args: unknown[] = [],
  options: { enabled?: boolean; refetchInterval?: number } = {},
) {
  const { client } = useWallet();
  return useQuery({
    queryKey: ["read", component, arm, args],
    enabled: Boolean(client) && (options.enabled ?? true),
    refetchInterval: options.refetchInterval,
    queryFn: async () => {
      const raw = await client!.read_component_json(
        component,
        arm,
        JSON.stringify(args),
      );
      const envelope = parseRead<T>(raw);
      return unwrap<T>(envelope.data);
    },
  });
}

export function useUriRead<T = State>(
  uri: string | undefined,
  arm: string,
  args: unknown[] = [],
  options: { enabled?: boolean; refetchInterval?: number } = {},
) {
  const { client } = useWallet();
  return useQuery({
    queryKey: ["read-uri", uri, arm, args],
    enabled: Boolean(client && uri) && (options.enabled ?? true),
    refetchInterval: options.refetchInterval,
    queryFn: async () => {
      const raw = await client!.read_uri_json(uri!, arm, JSON.stringify(args));
      const envelope = parseRead<T>(raw);
      return unwrap<T>(envelope.data);
    },
  });
}

export async function writeComponent(
  client: Rsure,
  component: string,
  arm: string,
  args: unknown[],
  ownerFirst = true,
): Promise<WriteEnvelope<unknown>> {
  const raw = await client.write_component_json(
    component,
    arm,
    JSON.stringify(args),
    ownerFirst,
  );
  return parseWrite(raw);
}

export async function writeUri(
  client: Rsure,
  uri: string,
  arm: string,
  args: unknown[],
  ownerFirst = true,
): Promise<WriteEnvelope<unknown>> {
  const raw = await client.write_uri_json(uri, arm, JSON.stringify(args), ownerFirst);
  return parseWrite(raw);
}

/**
 * The registry URI a create/register/submit arm replied with. Write replies are the
 * decoded reply array; `Reply::Ok` strips the leading `true`, so the URI is the last
 * `rho:id:` string.
 */
export function createdUri(data: unknown): string | undefined {
  const value = unwrap(data);
  if (!Array.isArray(value)) return undefined;
  for (let index = value.length - 1; index >= 0; index -= 1) {
    const item = value[index];
    if (typeof item === "string" && item.startsWith("rho:id:")) return item;
  }
  return undefined;
}

export function shortUri(uri: string | null | undefined, size = 12): string {
  if (!uri) return "—";
  return uri.length > size * 2
    ? `${uri.slice(0, size)}…${uri.slice(-6)}`
    : uri;
}


export function mapEntries<T = unknown>(data: unknown): Array<[string, T]> {
  const map = asMap(data) as Record<string, T>;
  return Object.entries(map);
}
