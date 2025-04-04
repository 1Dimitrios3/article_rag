import * as React from "react";
import { Select } from "radix-ui";
import { SelectItem } from "./selectItem";
import { ChevronDownIcon, ChevronUpIcon } from "@radix-ui/react-icons";
import { SelectListProps } from "~/types";

export const SelectList = <T extends string>({
  options,
  selectedValue,
  onChange,
  placeholder = "Select an option",
  disabled,
  className
}: SelectListProps<T>) => {
  const triggerClasses = `inline-flex items-center justify-center gap-[5px] rounded-md bg-zinc-900 px-[15px] text-[13px] border border-gray-700 shadow-sm outline-none transition-all hover:bg-zinc-800 focus:ring-1 focus:ring-violet-500 focus:ring-offset-2 focus:ring-offset-zinc-900 ${className || "h-[35px]"}`;
  return (
    <Select.Root value={selectedValue} disabled={disabled} onValueChange={onChange}>
      <Select.Trigger
        className={triggerClasses}
        aria-label="Select"
      >
        {/* This ensures default state text is soft grey, while keeping placeholder slightly dimmer */}
        <Select.Value
          placeholder={placeholder}
          className="data-[placeholder]:text-gray-500 text-gray-400"
        />
        <Select.Icon className="text-gray-400">
          <ChevronDownIcon />
        </Select.Icon>
      </Select.Trigger>

      <Select.Portal>
        <Select.Content
          className="
            overflow-hidden 
            rounded-md 
            bg-zinc-900 
            border border-gray-700 
            shadow-lg
          "
        >
          <Select.ScrollUpButton className="flex h-[25px] items-center justify-center bg-zinc-900 text-gray-400">
            <ChevronUpIcon />
          </Select.ScrollUpButton>

          <Select.Viewport className="p-[5px]">
            {options.map((option) => (
              <SelectItem
                key={option.value}
                value={option.value}
                disabled={option.disabled}
                className="
                  px-3 py-2 
                  text-gray-400
                  cursor-pointer 
                  transition-all 
                  hover:bg-zinc-800 
                  hover:text-gray-100 
                  disabled:text-gray-500
                "
              >
                {option.label}
              </SelectItem>
            ))}
          </Select.Viewport>

          <Select.ScrollDownButton className="flex h-[25px] items-center justify-center bg-zinc-900 text-gray-400">
            <ChevronDownIcon />
          </Select.ScrollDownButton>
        </Select.Content>
      </Select.Portal>
    </Select.Root>
  );
};

export default SelectList;
