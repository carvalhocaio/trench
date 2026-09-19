export type FieldErrors = Record<string, string>;

export type FormState = {
  fieldErrors: FieldErrors;
  formError: string | null;
  success: boolean;
};

export const initialFormState: FormState = {
  fieldErrors: {},
  formError: null,
  success: false,
};
