import test from "node:test";
import assert from "node:assert/strict";
import {
  readFavorites,
  toggleFavorite,
  FAVORITES_KEY,
} from "../src/lib/favorites.mjs";
function storage(initial = null) {
  let value = initial;
  return {
    getItem: () => value,
    setItem: (key, v) => {
      assert.equal(key, FAVORITES_KEY);
      value = v;
    },
  };
}
test("favorites persist and toggle using author/name identity", () => {
  const s = storage();
  assert.equal(readFavorites(s).size, 0);
  toggleFavorite(s, "anthropic/pdf");
  toggleFavorite(s, "openai/pdf");
  assert.deepEqual([...readFavorites(s)], ["anthropic/pdf", "openai/pdf"]);
  toggleFavorite(s, "anthropic/pdf");
  assert.deepEqual([...readFavorites(s)], ["openai/pdf"]);
});
test("invalid storage is handled safely and duplicates are removed", () => {
  for (const value of ["invalid", "null", "{}", "42"])
    assert.equal(readFavorites(storage(value)).size, 0);
  assert.deepEqual(
    [...readFavorites(storage('["a/b","a/b",null,4,"bad"]'))],
    ["a/b"],
  );
});
test("read restrictions are safe and write failure propagates without claiming success", () => {
  assert.equal(
    readFavorites({
      getItem: () => {
        throw Error("denied");
      },
    }).size,
    0,
  );
  const s = {
    getItem: () => null,
    setItem: () => {
      throw Error("quota");
    },
  };
  assert.throws(() => toggleFavorite(s, "a/b"), /quota/);
});
