import { cn } from "@/lib/utils";
import { ButtonHTMLAttributes, forwardRef } from "react";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary";
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "primary", ...props }, ref) => (
    <button
      ref={ref}
      className={cn(
        "inline-flex items-center justify-center px-4 py-2 rounded-md font-medium text-sm transition-colors",
        "disabled:opacity-50 disabled:pointer-events-none",
        variant === "primary" && "bg-black text-white hover:bg-gray-800",
        variant === "secondary" && "bg-gray-100 text-gray-900 hover:bg-gray-200",
        className,
      )}
      {...props}
    />
  ),
);
Button.displayName = "Button";
