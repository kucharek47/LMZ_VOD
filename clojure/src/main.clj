(ns main
  (:require [ring.adapter.jetty :refer [run-jetty]]
            [cheshire.core :as json]))

(defn zlicz_tagi [historia]
  (loop [lista_pozycji historia
         licznik {}]
    (if (empty? lista_pozycji)
      licznik
      (let [film (first lista_pozycji)
            tagi (get film "tagi")
            nowy_licznik (reduce (fn [acc tag] (update acc tag (fnil inc 0))) licznik tagi)]
        (recur (rest lista_pozycji) nowy_licznik)))))

(defn filtruj_nieogladane [filmy historia_ids]
  (filter (fn [film] (not (contains? historia_ids (get film "id")))) filmy))

(defn oblicz_punkty [film wagi_tagow]
  (let [tagi (get film "tagi")
            punkty (reduce + (map #(get wagi_tagow % 0) tagi))]
    (assoc film "punkty" punkty)))

(defn zastosuj_transformacje [funkcja_mapujaca kolekcja]
  (map funkcja_mapujaca kolekcja))

(defn obsluga_analizy [req]
  (let [cialo (json/parse-string (slurp (:body req)))
        historia (get cialo "historia")
        wszystkie_filmy (get cialo "filmy")
        historia_ids (set (map #(get % "id") historia))
        wagi (zlicz_tagi historia)
        nieogladane (filtruj_nieogladane wszystkie_filmy historia_ids)
        ocenione (zastosuj_transformacje #(oblicz_punkty % wagi) nieogladane)
        odfiltrowane_z_punktami (filter #(> (get % "punkty") 0) ocenione)
        posortowane (sort-by #(get % "punkty") > odfiltrowane_z_punktami)
        wynik (take 5 posortowane)]
    {:status 200
     :headers {"Content-Type" "application/json"}
     :body (json/generate-string wynik)}))

(defn router [req]
  (if (and (= (:uri req) "/api/analyze")
           (= (:request-method req) :post))
    (obsluga_analizy req)
    {:status 404
     :body "Nie znaleziono"}))

(defn -main []
  (run-jetty router {:port 3000
                     :join? false}))