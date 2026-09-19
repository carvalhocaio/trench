export const FIELD_CLASS =
  "block w-full rounded-md border border-zinc-300 px-3 py-2 text-sm text-zinc-900 focus:border-nfl-navy focus:outline-none";

export function FormField({
  label,
  htmlFor,
  error,
  children,
}: {
  label: string;
  htmlFor: string;
  error?: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <label htmlFor={htmlFor} className="block text-sm font-medium text-zinc-700">
        {label}
      </label>
      <div className="mt-1">{children}</div>
      {error && <p className="mt-1 text-sm text-nfl-red">{error}</p>}
    </div>
  );
}

export function NumberField({
  label,
  name,
  error,
  defaultValue,
  step,
  allowNegative,
}: {
  label: string;
  name: string;
  error?: string;
  defaultValue?: string | number;
  step?: number;
  allowNegative?: boolean;
}) {
  return (
    <FormField label={label} htmlFor={name} error={error}>
      <input
        type="number"
        id={name}
        name={name}
        min={allowNegative ? undefined : 0}
        step={step}
        placeholder="0"
        defaultValue={defaultValue}
        className={FIELD_CLASS}
      />
    </FormField>
  );
}

export function FormFeedback({
  formError,
  success,
  successMessage,
}: {
  formError: string | null;
  success: boolean;
  successMessage: string;
}) {
  if (formError) {
    return <p className="text-sm text-nfl-red">{formError}</p>;
  }
  if (success) {
    return <p className="text-sm text-emerald-600">{successMessage}</p>;
  }
  return null;
}
