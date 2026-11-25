// Helpers that read the backend's own /openapi.json, so the Evaluation form always
// matches the real request model (field names, ranges, optional/required).

export function resolveRef(openapi, node) {
  let cur = node;
  let guard = 0;
  while (cur && cur.$ref && guard++ < 20) {
    const name = cur.$ref.split("/").pop();
    cur = openapi?.components?.schemas?.[name];
  }
  return cur || {};
}

// strips Optional[...] / allOf wrappers and reports whether the field may be null
export function unwrap(openapi, node) {
  const s = resolveRef(openapi, node);
  const variants = s.anyOf || s.oneOf;
  if (variants) {
    const nullable = variants.some((v) => v.type === "null");
    const real = variants.find((v) => v.type !== "null");
    const inner = real ? unwrap(openapi, real).schema : {};
    return { schema: { ...inner, description: s.description ?? inner.description }, nullable };
  }
  if (s.allOf && s.allOf.length) {
    const inner = unwrap(openapi, s.allOf[0]);
    return {
      schema: { ...inner.schema, description: s.description ?? inner.schema.description },
      nullable: inner.nullable,
    };
  }
  return { schema: s, nullable: false };
}

export function numberBounds(schema) {
  const lo = schema.minimum ?? (schema.exclusiveMinimum !== undefined ? schema.exclusiveMinimum + 1 : undefined);
  const hi = schema.maximum ?? (schema.exclusiveMaximum !== undefined ? schema.exclusiveMaximum - 1 : undefined);
  return { lo, hi };
}

function numberExample(schema) {
  const { lo, hi } = numberBounds(schema);
  let v = 0;
  if (lo !== undefined && hi !== undefined) v = (lo + hi) / 2;
  else if (lo !== undefined) v = lo;
  else if (hi !== undefined) v = hi;
  return schema.type === "integer" ? Math.round(v) : v;
}

function example(openapi, node, opts, depth = 0) {
  if (depth > 6) return null;
  const schema = resolveRef(openapi, node);

  if (schema.example !== undefined) return schema.example;

  const variants = schema.anyOf || schema.oneOf;
  if (variants) {
    const real = variants.find((v) => v.type !== "null");
    return real ? example(openapi, real, opts, depth + 1) : null;
  }
  if (schema.allOf && schema.allOf.length) return example(openapi, schema.allOf[0], opts, depth + 1);
  if (schema.enum) return schema.enum[0];
  if (schema.const !== undefined) return schema.const;

  if (schema.properties || schema.type === "object") {
    const props = schema.properties || {};
    const required = new Set(schema.required || []);
    const out = {};
    for (const [key, prop] of Object.entries(props)) {
      const nullable = (prop.anyOf || []).some((v) => v.type === "null");
      const optional = !required.has(key);
      if (optional && nullable && !opts.includeOptional) {
        out[key] = prop.default !== undefined ? prop.default : null;
      } else if (prop.default !== undefined && !(opts.includeOptional && nullable)) {
        out[key] = prop.default;
      } else {
        out[key] = example(openapi, prop, opts, depth + 1);
      }
    }
    return out;
  }

  switch (schema.type) {
    case "string":
      return schema.default !== undefined ? schema.default : "";
    case "integer":
    case "number":
      return schema.default !== undefined ? schema.default : numberExample(schema);
    case "boolean":
      return schema.default !== undefined ? schema.default : false;
    case "array":
      if (opts.emptyArrays) return [];
      return schema.items ? [example(openapi, schema.items, opts, depth + 1)] : [];
    default:
      return null;
  }
}

// a fresh value for one schema node (used by the "Add" buttons)
export const exampleFor = (openapi, node, opts = {}) =>
  example(openapi, node, { includeOptional: true, emptyArrays: true, ...opts });

// the starting value of the whole form
export function templateFromOpenApi(openapi, schemaName, opts = {}) {
  const root = openapi?.components?.schemas?.[schemaName];
  if (!root) return null;
  return example(openapi, root, { includeOptional: true, emptyArrays: true, ...opts });
}