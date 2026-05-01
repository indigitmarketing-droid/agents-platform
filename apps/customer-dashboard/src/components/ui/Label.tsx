import { cn } from "@/lib/utils";
import { LabelHTMLAttributes } from "react";

export function Label({ className, ...props }: LabelHTMLAttributes<HTMLLabelElement>) {
  return (
    <label
      className={cn("text-sm font-medium text-gray-700 block mb-1", className)}
      {...props}
    />
  );
}
