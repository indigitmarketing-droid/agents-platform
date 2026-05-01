import { cn } from "@/lib/utils";
import { InputHTMLAttributes, forwardRef } from "react";

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...props }, ref) => (
    <input
      ref={ref}
      className={cn(
        "w-full px-3 py-2 border border-gray-300 rounded-md text-sm",
        "focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent",
        className,
      )}
      {...props}
    />
  ),
);
Input.displayName = "Input";
