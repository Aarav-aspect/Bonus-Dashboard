-- CreateTable
CREATE TABLE "public"."user_preference" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "sectors" TEXT[],
    "regions" TEXT[],
    "services" TEXT[],
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "user_preference_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "user_preference_userId_key" ON "public"."user_preference"("userId");

-- AddForeignKey
ALTER TABLE "public"."user_preference" ADD CONSTRAINT "user_preference_userId_fkey" FOREIGN KEY ("userId") REFERENCES "public"."user"("id") ON DELETE CASCADE ON UPDATE CASCADE;
