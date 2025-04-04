import * as React from "react";
import { Select } from "radix-ui";
import classNames from "classnames";
import { CheckIcon } from "@radix-ui/react-icons";

export interface SelectItemProps
  extends React.ComponentPropsWithRef<typeof Select.Item> {
  className?: string;
  children?: React.ReactNode;
}

export const SelectItem = React.forwardRef<
    HTMLDivElement,
  SelectItemProps
>(({ children, className, ...props }, ref) => {
  return (
    <Select.Item
    className={classNames(
        "relative flex h-[25px] select-none items-center rounded-[3px] pl-[25px] pr-[35px] text-[13px] leading-none text-violet11 data-[disabled]:pointer-events-none data-[highlighted]:bg-violet9 data-[disabled]:text-mauve8 data-[highlighted]:text-violet1 data-[highlighted]:outline-none",
        className,
    )}
    {...props}
    ref={ref}
>
    <Select.ItemText>{children}</Select.ItemText>
    <Select.ItemIndicator className="absolute left-0 inline-flex w-[25px] items-center justify-center">
        <CheckIcon />
    </Select.ItemIndicator>
</Select.Item>
  );
});

SelectItem.displayName = "SelectItem";