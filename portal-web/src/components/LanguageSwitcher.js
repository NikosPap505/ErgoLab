import React from "react";
import { useTranslation } from "react-i18next";

const LanguageSwitcher = () => {
  const { i18n, t } = useTranslation();

  const changeLanguage = (lng) => {
    i18n.changeLanguage(lng);
    localStorage.setItem("language", lng);
  };

  return (
    <div className="flex items-center space-x-2">
      <span className="text-sm text-gray-600 dark:text-gray-400">
        {t("common.language")}:
      </span>
      <div className="flex bg-gray-200 dark:bg-gray-700 rounded-lg p-1">
        <button
          onClick={() => changeLanguage("el")}
          className={`px-3 py-1 text-sm font-medium rounded-md transition-colors ${
            i18n.language === "el"
              ? "bg-white dark:bg-gray-800 text-indigo-600 dark:text-indigo-400 shadow-sm"
              : "text-gray-700 dark:text-gray-300 hover:text-indigo-600"
          }`}
        >
          🇬🇷 ΕΛ
        </button>
        <button
          onClick={() => changeLanguage("en")}
          className={`px-3 py-1 text-sm font-medium rounded-md transition-colors ${
            i18n.language === "en"
              ? "bg-white dark:bg-gray-800 text-indigo-600 dark:text-indigo-400 shadow-sm"
              : "text-gray-700 dark:text-gray-300 hover:text-indigo-600"
          }`}
        >
          🇬🇧 EN
        </button>
      </div>
    </div>
  );
};

export default LanguageSwitcher;
